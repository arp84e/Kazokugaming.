import { createBrowserClient } from '@supabase/ssr';

// Este cliente se utilizará principalmente en componentes con 'use client'
export const createClient = () =>
  createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
