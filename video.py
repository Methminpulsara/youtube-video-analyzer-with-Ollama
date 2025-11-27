from langchain_ollama import ChatOllama
from langchain_community.document_loaders import YoutubeLoader
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
from fastapi import FastAPI

llm = ChatOllama(model="llama3.2:3b")

analysis_prompt = ChatPromptTemplate.from_template(
    """
    you are an expert content analyst.
    analyze the following video transcript.

    Extract:
    - main topics covered
    - positive insights  
    - summary

    Transcript:
    {transcript}
    """
)

loader = YoutubeLoader.from_youtube_url(
    "https://youtu.be/-Yj1At289rw?si=wgHCePrBGGrP0XuJ",
    add_video_info=False
)

docs = loader.load()
transcript = docs[0].page_content

an_chain = analysis_prompt | llm
result = an_chain.invoke({"transcript": transcript},)


print(result)