from database import get_book_details, save_chapters
from chapter_splitter import split_chapters

book_id,filename,file_contents,character_count, created_at=get_book_details("1acec9f5-74e1-4bca-928e-3101e4f30cf6")
output_chapters_list=split_chapters(file_contents)
save_chapters(book_id,output_chapters_list)
print("Number of chapter is:", len(output_chapters_list))
print(file_contents[0:1000])
for i,chapter in enumerate(output_chapters_list):
    print(f"Source number for chapter {i+1} is: ",chapter["source_number"])
    print(f"The title for chapter {i+1} is: ",chapter["title"])