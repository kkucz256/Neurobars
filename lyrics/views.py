from django.shortcuts import render
from django.apps import apps
from django.http import JsonResponse
from .src.llm_service import ask_llm_rag, generate_qdrant_query