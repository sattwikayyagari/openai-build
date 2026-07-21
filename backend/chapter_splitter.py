import re

heading_pattern=r"^CHAPTER\s+(?P<number>\d+|[IVXLCDM]+)(?:\s*:\s*(?P<title>.+))?$"
uppercase_headings_pattern=r"^[     ]*(?P<title>[A-Z]+[A-Z ,'\-''\"\"]*)[     ]*$"
def normalize_text(text: str)->str:
    text=text.removeprefix('\ufeff')
    text=text.replace('\r\n','\n').replace('\r','\n')
    lines=[line.rstrip() for line in text.split('\n')]
    text="\n".join(lines)
    text=re.sub(r'\n{3,}','\n\n',text)
    return text

def split_chapters(text: str)->list:
    normalized_text=normalize_text(text)
    output_headings=list(re.finditer(heading_pattern,normalized_text,re.IGNORECASE|re.MULTILINE))
    chapter_content=[]
    for i,chapter in enumerate(output_headings, start=1):
        chapter_dict={}
        chapter_dict["position"]=i
        chapter_dict["source_number"]=chapter.group("number")
        start_index=chapter.end()
        end_index=output_headings[i].start() if i<len(output_headings) else len(normalized_text)
        chapter_dict["title"]=chapter.group("title")
        chapter_dict["content"]=normalized_text[start_index:end_index].strip()
        chapter_content.append(chapter_dict)
    if chapter_content:
        return chapter_content
    else:
        table_contents_pattern=re.search(r"^[   ]*Table[    ]+of[   ]+contents[     ]*$",normalized_text,re.IGNORECASE|re.MULTILINE)
        if table_contents_pattern is not None:
            uppercase_headings_output=list(re.finditer(uppercase_headings_pattern,normalized_text,re.MULTILINE))
            story_headings=[]
            chapter_content=[]
            for i in uppercase_headings_output:
                if i.start()>table_contents_pattern.end():
                    story_headings.append(i)
            for i,chapter in enumerate(story_headings, start=1):
                chapter_dict={}
                chapter_dict["position"]=i
                chapter_dict["source_number"]=None
                start_index=chapter.end()
                end_index=story_headings[i].start() if i<len(story_headings) else len(normalized_text)
                chapter_dict["title"]=chapter.group("title")
                chapter_dict["content"]=normalized_text[start_index:end_index].strip()
                chapter_content.append(chapter_dict)
            return chapter_content
        else:
            return []


