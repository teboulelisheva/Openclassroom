export interface SuggestedMove {
  san: string;
  uci: string;
}

export interface ContextItem {
  opening: string;
  eco: string;
  text: string;
  source: string;
  score: number;
}

export interface Video {
  video_id: string;
  title: string;
  channel: string;
  description: string;
  published_at: string;
  url: string;
  embed_url: string;
  thumbnail: string;
}

export interface Evaluation {
  type: string; // 'cp' ou 'mate'
  value: number;
  best_move: string | null;
  depth: number;
  interpretation: string;
}

export interface AssistantResponse {
  fen: string;
  opening: string | null;
  is_theoretical: boolean;
  moves: SuggestedMove[];
  evaluation: Evaluation | null;
  context: ContextItem[];
  videos: Video[];
  errors: string[];
}
