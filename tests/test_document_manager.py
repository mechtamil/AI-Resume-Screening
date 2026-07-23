from services.document_manager import DocumentManager

file_path = input("Enter document path: ")

text = DocumentManager.read_document(file_path)

print()

print("=" * 60)

print("Preview")

print("=" * 60)

print(text[:1000])

print("=" * 60)