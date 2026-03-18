import { createClient } from '@supabase/supabase-js';

let supabaseInstance: ReturnType<typeof createClient> | null = null;

async function getSupabaseCredentials(): Promise<{ url: string; key: string }> {
  // 尝试从环境变量获取
  let url = process.env.COZE_SUPABASE_URL;
  let key = process.env.COZE_SUPABASE_ANON_KEY;

  // 如果环境变量不存在，尝试从workload identity获取
  if (!url || !key) {
    try {
      const response = await fetch('http://localhost:5000/api/env/supabase');
      if (response.ok) {
        const data = await response.json();
        url = data.url;
        key = data.key;
      }
    } catch (error) {
      console.error('Failed to fetch Supabase credentials:', error);
    }
  }

  if (!url || !key) {
    throw new Error('Supabase credentials not found');
  }

  return { url, key };
}

export async function getSupabaseClient() {
  if (supabaseInstance) {
    return supabaseInstance;
  }

  const { url, key } = await getSupabaseCredentials();
  supabaseInstance = createClient(url, key);
  return supabaseInstance;
}
