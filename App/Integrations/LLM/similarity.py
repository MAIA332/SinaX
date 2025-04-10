from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Any

class QuestionSimilarity:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.similarity_threshold = 0.85  # Adjust this threshold as needed

    def calculate_similarity(self, question1: str, question2: str) -> float:
        """
        Calculate similarity between two questions using cosine similarity
        """
        embeddings = self.model.encode([question1, question2])
        similarity = np.dot(embeddings[0], embeddings[1]) / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]))
        return float(similarity)

    def find_similar_question(self, question: str, cached_questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Find the most similar question in the cache
        Returns the cached QA pair if similarity is above threshold, None otherwise
        """
        best_match = None
        highest_similarity = 0.0

        for cached_qa in cached_questions:
            similarity = self.calculate_similarity(question, cached_qa['question'])
            if similarity > highest_similarity and similarity >= self.similarity_threshold:
                highest_similarity = similarity
                best_match = cached_qa
                best_match['similarity_score'] = similarity

        return best_match 