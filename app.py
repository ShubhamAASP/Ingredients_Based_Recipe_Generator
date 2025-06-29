from flask import Flask, render_template, request, jsonify, send_file, session
import os
import requests
import json
import datetime
import io
import base64
from fpdf import FPDF
from generate import generation_function

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session

# Pexels API configuration
PEXELS_API_KEY = "BGuL3QPGyoHAY9uuafJk27xxORGKnbJrEkdndndpE9smSYlM9OLv7lNs"
PEXELS_HEADERS = {
    'Authorization': PEXELS_API_KEY
}

# Feedback file path
FEEDBACK_FILE = 'feedback.json'

# Recipe session storage for downloading
RECIPE_CACHE = {}

def get_recipe_image(recipe_title):
    """Fetch an image related to the recipe from Pexels API"""
    clean_title = recipe_title.replace("title:", "").strip()
    query = clean_title if clean_title else "food recipe"
    
    url = f"https://api.pexels.com/v1/search?query={query}&per_page=1"
    
    try:
        response = requests.get(url, headers=PEXELS_HEADERS)
        if response.status_code == 200:
            data = response.json()
            if 'photos' in data and data['photos']:
                return data['photos'][0]['src']['medium']
        # Return a default food image if no specific image found
        return "https://images.pexels.com/photos/1640774/pexels-photo-1640774.jpeg"
    except Exception as e:
        print(f"Error fetching image: {e}")
        return "https://images.pexels.com/photos/1640774/pexels-photo-1640774.jpeg"

def parse_recipe(recipe_text):
    """Parse the recipe text into structured data with image"""
    sections = recipe_text.split("\n")
    recipe_data = {"sections": []}
    
    for section in sections:
        section = section.strip()
        if section.startswith("title:"):
            recipe_data["title"] = section.replace("title:", "").strip().capitalize()
            # Get image for the recipe
            recipe_data["image_url"] = get_recipe_image(section)
        elif section.startswith("ingredients:"):
            items = []
            for item in section.replace("ingredients:", "").split("--"):
                if item.strip():
                    items.append(item.strip().capitalize())
            recipe_data["sections"].append({"name": "INGREDIENTS", "items": items})
        elif section.startswith("directions:"):
            steps = []
            for step in section.replace("directions:", "").split("--"):
                if step.strip():
                    steps.append(step.strip().capitalize())
            recipe_data["sections"].append({"name": "DIRECTIONS", "items": steps})
    
    return recipe_data

def get_all_feedback():
    """Load feedback from JSON file"""
    if not os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, 'w') as f:
            json.dump({"feedback": []}, f)
        return []
    
    with open(FEEDBACK_FILE, 'r') as f:
        try:
            data = json.load(f)
            return data.get('feedback', [])
        except json.JSONDecodeError:
            return []

def save_feedback(feedback_data):
    """Save feedback to JSON file"""
    current_feedback = get_all_feedback()
    current_feedback.append(feedback_data)
    
    with open(FEEDBACK_FILE, 'w') as f:
        json.dump({"feedback": current_feedback}, f, indent=2)

def create_recipe_pdf(recipe_id):
    """Create a PDF for the recipe"""
    global RECIPE_CACHE
    
    # Try to get from session if not in memory cache
    if recipe_id not in RECIPE_CACHE and 'recipes' in session:
        session_recipes = session['recipes']
        for recipe in session_recipes:
            if recipe.get('id') == recipe_id:
                RECIPE_CACHE[recipe_id] = recipe
    
    if recipe_id not in RECIPE_CACHE:
        return None
    
    recipe = RECIPE_CACHE[recipe_id]
    pdf = FPDF()
    pdf.add_page()
    
    # Add title
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(190, 10, recipe['title'], 0, 1, 'C')
    pdf.ln(5)
    
    # Try to add the image
    try:
        image_url = recipe['image_url']
        response = requests.get(image_url)
        if response.status_code == 200:
            # Save image temporarily
            temp_dir = os.path.join(os.getcwd(), 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            img_temp = os.path.join(temp_dir, 'temp_recipe_img.jpg')
            
            with open(img_temp, 'wb') as img_file:
                img_file.write(response.content)
            
            # Add image to PDF
            if os.path.exists(img_temp):
                # Get image dimensions
                img_height = 0
                try:
                    from PIL import Image
                    img = Image.open(img_temp)
                    img_width, img_height = img.size
                    # Calculate the right height based on aspect ratio and width (190)
                    aspect_ratio = img_width / img_height
                    img_height = min(190 / aspect_ratio, 150)  # Limit height to 150
                except:
                    img_height = 150  # Default height if PIL not installed
                
                # Add image with proper position
                pdf.image(img_temp, x=10, y=pdf.get_y(), w=190, h=img_height)
                
                # Ensure enough space after image
                pdf.ln(img_height + 20)  # Add extra space to avoid overlap
                
                # Remove temporary image
                try:
                    os.remove(img_temp)
                except:
                    pass  # Ignore if we can't delete
    except Exception as e:
        print(f"Error adding image to PDF: {e}")
        pdf.ln(5)
    
    # Add sections
    for section in recipe['sections']:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(190, 10, section['name'], 0, 1, 'L')
        pdf.ln(2)
        
        pdf.set_font('Arial', '', 11)
        for idx, item in enumerate(section['items'], 1):
            try:
                # Clean the text to avoid encoding issues
                clean_item = ''.join(c if ord(c) < 128 else ' ' for c in item)
                
                if section['name'] == 'INGREDIENTS':
                    pdf.cell(190, 8, f"* {clean_item}", 0, 1)
                else:  # Directions
                    pdf.multi_cell(190, 8, f"{idx}. {clean_item}")
            except Exception as e:
                print(f"Error adding text to PDF: {e}")
                continue
            
        pdf.ln(5)
    
    # Footer
    pdf.set_font('Arial', 'I', 8)
    pdf.set_y(-15)
    pdf.cell(0, 10, f"Recipe Generator - Created on {datetime.datetime.now().strftime('%Y-%m-%d')}", 0, 0, 'C')
    
    try:
        # Return PDF as bytes
        return pdf.output(dest='S').encode('latin1')
    except Exception as e:
        print(f"Error generating PDF: {e}")
        # Fallback: try without encoding
        return pdf.output(dest='S')

@app.route('/')
def index():
    """Main page with feedback loaded initially"""
    feedback = get_all_feedback()
    current_year = datetime.datetime.now().year
    return render_template('index.html', feedback=feedback, year=current_year)

@app.route('/generate', methods=['POST'])
def generate():
    """Generate recipes based on ingredients"""
    ingredients = request.form.get('ingredients', '').strip()
    
    if not ingredients:
        return jsonify({"error": "No ingredients provided"})
    
    # Generate recipes
    generated_recipes = generation_function([ingredients], num_variations=3)
    
    # Parse and format recipes
    recipes = []
    global RECIPE_CACHE
    RECIPE_CACHE = {}  # Clear cache
    
    for variations in generated_recipes:
        for i, recipe_text in enumerate(variations):
            parsed_recipe = parse_recipe(recipe_text)
            # Generate a unique ID for this recipe
            recipe_id = f"recipe_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{i}"
            parsed_recipe['id'] = recipe_id
            # Store in cache for download
            RECIPE_CACHE[recipe_id] = parsed_recipe
            recipes.append(parsed_recipe)
    
    # Store in session for persistence
    session['recipes'] = recipes
    
    return jsonify({"recipes": recipes})

@app.route('/download/<recipe_id>', methods=['GET'])
def download_recipe(recipe_id):
    """Download a recipe as PDF"""
    try:
        pdf_bytes = create_recipe_pdf(recipe_id)
        
        if not pdf_bytes:
            return jsonify({"error": "Recipe not found"}), 404
        
        # Create a BytesIO object from the PDF bytes
        pdf_io = io.BytesIO(pdf_bytes)
        pdf_io.seek(0)
        
        recipe_title = RECIPE_CACHE[recipe_id]['title'].replace(' ', '_')
        sanitized_title = ''.join(c for c in recipe_title if c.isalnum() or c in ['_', '-'])
        
        return send_file(
            pdf_io,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{sanitized_title}.pdf"
        )
    except Exception as e:
        print(f"Error in download route: {e}")
        return jsonify({"error": "Failed to generate PDF. Please try again."}), 500

@app.route('/recipe/<recipe_id>', methods=['GET'])
def get_recipe_json(recipe_id):
    """Get recipe data as JSON or HTML (fallback for PDF download)"""
    global RECIPE_CACHE
    
    # Try to get from session if not in memory cache
    if recipe_id not in RECIPE_CACHE and 'recipes' in session:
        session_recipes = session['recipes']
        for recipe in session_recipes:
            if recipe.get('id') == recipe_id:
                RECIPE_CACHE[recipe_id] = recipe
    
    if recipe_id not in RECIPE_CACHE:
        return jsonify({"error": "Recipe not found"}), 404
    
    recipe = RECIPE_CACHE[recipe_id]
    
    # Check if the request wants JSON or HTML
    if request.headers.get('Accept', '').find('application/json') != -1:
        return jsonify(recipe)
    
    # Render HTML view for browser requests
    return render_template('recipe.html', recipe=recipe)

@app.route('/feedback', methods=['POST'])
def add_feedback():
    name = request.form.get('name', '').strip()
    recipe_title = request.form.get('recipe_title', '').strip()
    rating = request.form.get('rating', '0')
    comment = request.form.get('comment', '').strip()
    
    if not name or not recipe_title or not comment:
        return jsonify({"error": "Missing required fields"}), 400
    
    # Create feedback entry
    feedback_data = {
        "name": name,
        "recipe_title": recipe_title,
        "rating": rating,
        "comment": comment,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        save_feedback(feedback_data)
        all_feedback = get_all_feedback()
        return jsonify({"success": True, "feedback": all_feedback})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/about-ai')
def about_ai():
    """About our AI page"""
    current_year = datetime.datetime.now().year
    return render_template('about_ai.html', year=current_year)

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True) 