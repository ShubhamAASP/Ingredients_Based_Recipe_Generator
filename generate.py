from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

MODEL_NAME_OR_PATH = r"C:\shubham2144\Mini_Project\050425\t5-recipe-model-local"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME_OR_PATH, use_fast=True)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME_OR_PATH)

# Generation configuration
prefix = "items: "
generation_kwargs = {
    "max_length": 1024,
    "min_length": 100,
    "no_repeat_ngram_size": 3,
    "do_sample": True,
    "top_k": 60,
    "top_p": 0.95
}

# Token cleanup and formatting
special_tokens = tokenizer.all_special_tokens
tokens_map = {
    "<sep>": "--",
    "<section>": "\n"
}

def skip_special_tokens(text, special_tokens):
    for token in special_tokens:
        text = text.replace(token, "")
    return text

def target_postprocessing(texts, special_tokens):
    if not isinstance(texts, list):
        texts = [texts]
    new_texts = []
    for text in texts:
        text = skip_special_tokens(text, special_tokens)
        for k, v in tokens_map.items():
            text = text.replace(k, v)
        new_texts.append(text)
    return new_texts

# Generate multiple recipe variations for each input
def generation_function(texts, num_variations=3):
    _inputs = texts if isinstance(texts, list) else [texts]
    inputs = [prefix + inp for inp in _inputs]

    results = []
    for input_text in inputs:
        input_enc = tokenizer(
            input_text,
            max_length=256,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )
        input_ids = input_enc.input_ids
        attention_mask = input_enc.attention_mask

        recipes = []
        for _ in range(num_variations):
            output_ids = model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                **generation_kwargs
            )
            generated = output_ids
            recipe = target_postprocessing(
                tokenizer.batch_decode(generated, skip_special_tokens=False),
                special_tokens
            )[0]
            recipes.append(recipe)
        results.append(recipes)
    
    return results

# === Run Interactive Input ===

if __name__ == "__main__":
    print("🔸 Recipe Generator 🔸")
    user_input = input("Enter your ingredients (comma-separated): ").strip()

    if user_input:
        generated = generation_function([user_input], num_variations=3)

        for idx, variations in enumerate(generated):
            print(f"\n🔹 Ingredient Set #{idx + 1}")
            for i, recipe in enumerate(variations):
                print(f"\n✨ Recipe Variation {i + 1}")
                print("-" * 40)
                for section in recipe.split("\n"):
                    section = section.strip()
                    if section.startswith("title:"):
                        print(f"[TITLE]: {section.replace('title:', '').strip().capitalize()}")
                    elif section.startswith("ingredients:"):
                        print(f"[INGREDIENTS]:")
                        for j, item in enumerate(section.replace("ingredients:", "").split("--")):
                            print(f"  - {j + 1}: {item.strip().capitalize()}")
                    elif section.startswith("directions:"):
                        print(f"[DIRECTIONS]:")
                        for j, step in enumerate(section.replace("directions:", "").split("--")):
                            print(f"  - {j + 1}: {step.strip().capitalize()}")
                print("-" * 40)
    else:
        print("⚠️ No ingredients entered.")
