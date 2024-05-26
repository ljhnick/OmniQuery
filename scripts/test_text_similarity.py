from openai import OpenAI
import numpy as np


client = OpenAI()
def calculate_embeddings(text, model="text-embedding-3-small"):
    return client.embeddings.create(input = [text], model=model).data[0].embedding


def main():
    text1 = "Mai Lan is a Vietnamese restaurant."
    text2 = "Mai Lan opens at 10:30 AM on Monday."

    embedding1 = calculate_embeddings(text1)
    embedding2 = calculate_embeddings(text2)

    similarity = np.dot(embedding1, embedding2)
    print(similarity)


if __name__ == "__main__":
    main()
