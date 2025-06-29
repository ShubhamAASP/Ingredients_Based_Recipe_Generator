# Recipe Generator with Images, Feedback, and PDF Downloads

This web application takes a list of ingredients as input and generates 3 different recipe variations with matching images from Pexels API. Users can also provide feedback on recipes and download them as PDFs.

## Features

- Generate recipes from a list of comma-separated ingredients
- AI-powered recipe generation using T5 model
- Automatic image fetching based on recipe titles using Pexels API
- Download recipes as beautifully formatted PDFs
- Fallback options: recipes can be viewed and printed directly in browser if PDF download fails
- Customer feedback system with ratings and comments
- Beautiful, responsive web interface with animations
- Mobile-friendly design
- Session-based recipe storage for persistence between page refreshes

## Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Start the Flask server:

```bash
python app.py
```

2. Open your browser and navigate to `http://127.0.0.1:5000/`
3. Enter a comma-separated list of ingredients (e.g., "chicken, rice, tomatoes, onions")
4. Click "Generate Recipes" to get 3 recipe variations with matching images
5. Click "Download Recipe PDF" to save any recipe as a PDF file
   - If PDF download doesn't work, the button will change to "View & Print Recipe" to view the recipe in the browser
6. Provide feedback on recipes using the feedback form

## Project Structure

- `app.py`: Flask web application
- `generate.py`: Recipe generation functionality
- `templates/index.html`: Main web frontend
- `templates/recipe.html`: Single recipe view for printing
- `t5-recipe-model-local/`: Model files for recipe generation
- `feedback.json`: Storage for user feedback
- `temp/`: Temporary directory for image processing

## Dependencies

- Flask: Web framework
- Transformers: For the T5 recipe generation model
- Requests: For Pexels API integration
- PyTorch: For model inference
- FPDF: For generating PDF downloads

## Credits

- Recipe generation model: [flax-community/t5-recipe-generation](https://huggingface.co/flax-community/t5-recipe-generation)
- Images provided by [Pexels API](https://www.pexels.com/api/)
- Icons from [Font Awesome](https://fontawesome.com/)
- Animations from [Animate.css](https://animate.style/) 