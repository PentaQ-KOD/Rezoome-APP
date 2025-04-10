from together import Together

# Initialize Together API client
client = Together()  # เปลี่ยนเป็น API Key ของคุณ


def classify_text(text):
    prompt = f"""Classify the following text:

{text}

Possible classes: [Resume/CV, Job Description, Job Application, Interview, Offer]  # Replace with your classes

Classification:"""

    # Call Together API
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        messages=[{"role": "user", "content": prompt}],
    )

    # Extract the response
    classification = response.choices[0].message.content.strip()

    # Split the response to get only the classification label
    lines = classification.split("\n")
    for line in lines:
        if line.startswith("Classification:"):
            classification_label = line.replace("Classification:", "").strip()
            return classification_label

    # If no classification label is found, return None
    return None
