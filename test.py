from rag import answer

q = "Summarize what this document is about."
resp, hits = answer(q)

print("\n=== ANSWER ===\n")
print(resp)

print("\n=== SOURCES USED ===\n")
for i, (_, meta) in enumerate(hits, start=1):
    print(f"[{i}] {meta['source']} (chunk {meta['chunk']})")
