export interface Profile {
  id: string;
  username: string;
  full_name: string | null;
  avatar_url: string | null;
  role: 'admin' | 'editor' | 'author';
  bio: string | null;
  twitter_url: string | null;
  created_at: string;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  parent_id: number | null;
  created_at: string;
}

export interface ReviewScores {
  gameplay: number;
  graphics: number;
  sound: number;
  performance: number;
  innovation: number;
  final: number;
}

export interface Article {
  id: string;
  title: string;
  slug: string;
  excerpt: string | null;
  content: string;
  image_url: string | null;
  author_id: string | null;
  category_id: number | null;
  tags: string[];
  status: 'draft' | 'published' | 'scheduled';
  read_time: number;
  review_scores: ReviewScores | null; // Flexible para cuando sea una review
  seo_title: string | null;
  seo_description: string | null;
  view_count: number;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}
