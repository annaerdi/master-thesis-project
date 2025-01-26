import textdistance


"""
These comparisons are the bases for plagiarism checks, so the info it can provide shows how similar the two files are.
It might be useful if combined with other evaluation methods.
"""

def textdistance_similarity_jaccard(file1, file2):
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        content1 = f1.read()
        content2 = f2.read()
    
    # Use Jaccard similarity as an example
    similarity = textdistance.jaccard(content1, content2)
    return similarity

def textdistance_similarity_cosine(file1, file2):
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        content1 = f1.read()
        content2 = f2.read()
    
    # Use cosine distance
    similarity = textdistance.cosine(content1, content2)
    return similarity
    
def textdistance_similarity_levenshtein(file1, file2):
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        content1 = f1.read()
        content2 = f2.read()
    
    # Return the normalized levenshtein distance
    similarity = 1 - textdistance.levenshtein.normalized_distance(content1, content2)
    return similarity

def textdistance_similarity_sorensen(file1, file2):
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        content1 = f1.read()
        content2 = f2.read()
    
    similarity = textdistance.sorensen(content1, content2)
    return similarity


file1 = "../playbooks/llm/admin1_a.yml"
file2 = "../playbooks/manual/admin1.yml"
similarity_cosine = textdistance_similarity_cosine(file1, file2)
similarity_jaccard = textdistance_similarity_jaccard(file1, file2)
similarity_levenshtein = textdistance_similarity_levenshtein(file1, file2)
similarity_sorensen = textdistance_similarity_sorensen(file1, file2)
print(f"Similarity cosine: {similarity_cosine * 100:.2f}%")
print(f"Similarity jaccard: {similarity_jaccard * 100:.2f}%")
print(f"Similarity levenshtein: {similarity_levenshtein * 100:.2f}%")
print(f"Similarity sorensen: {similarity_sorensen * 100:.2f}%")
