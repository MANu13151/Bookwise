from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from functools import lru_cache
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from contextlib import asynccontextmanager

# -----------------------------
# Request Schema
# -----------------------------
class QueryRequest(BaseModel):
    query: str
    top_n: int = 5

# -----------------------------
# Data Cleaning
# -----------------------------
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.str.strip().str.lower()
    df = df.dropna(subset=['name', 'combine_feat'])
    df['name'] = df['name'].str.strip()
    df['combine_feat'] = df['combine_feat'].str.strip()
    df = df.drop_duplicates(subset=['name', 'combine_feat'])
    return df.reset_index(drop=True)

# -----------------------------
# Load Data & Model
# -----------------------------
@lru_cache()
def load_data(csv_path: str = "preprocessed.csv") -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = clean_data(df)
    return df

@lru_cache()
def load_model(model_name: str = 'all-MiniLM-L6-v2') -> SentenceTransformer:
    return SentenceTransformer(model_name)

# -----------------------------
# FastAPI App Initialization
# -----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    df = load_data()
    model = load_model()

    if 'embedding' not in df.columns or df['embedding'].isnull().any():
        print("[INFO] Computing embeddings from 'combine_feat'...")
        embeddings = model.encode(df['combine_feat'].tolist(), show_progress_bar=True)
        df['embedding'] = embeddings.tolist()
        df.to_csv("preprocessed_with_embeddings.csv", index=False)
        print("[INFO] Saved updated CSV with embeddings.")

    app.state.df = df
    app.state.model = model
    yield

app = FastAPI(
    title="BookWise Backend API",
    description="AI-powered book recommendation endpoints",
    version="0.1.0",
    lifespan=lifespan
)

# -----------------------------
# CORS Middleware
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://172.16.14.248:8501"],  # Or restrict: ["http://localhost:8501"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Recommend Endpoint
# -----------------------------
@app.post("/recommend")
def recommend(request: QueryRequest):
    df = app.state.df
    model = app.state.model

    top_n = min(request.top_n, len(df))

    user_emb = model.encode([request.query])[0]
    embeddings = np.vstack(df['embedding'].apply(np.array).values)
    sims = cosine_similarity([user_emb], embeddings)[0]

    top_indices = np.argsort(sims)[-top_n:][::-1]
    results = df.iloc[top_indices][['name', 'authors']]
    recommendations = [
        {"title": row['name'], "description": f"By {row['authors']}"}
        for _, row in results.iterrows()
    ]

    return {"recommendations": recommendations}
