import { createClient, SupabaseClient } from '@supabase/supabase-js';

let supabaseInstance: SupabaseClient | null = null;

/**
 * 获取 Supabase 客户端
 * 环境变量通过平台配置，直接从 process.env 读取
 */
export function getSupabaseClient(): SupabaseClient {
  if (supabaseInstance) {
    return supabaseInstance;
  }

  const url = process.env.COZE_SUPABASE_URL;
  const anonKey = process.env.COZE_SUPABASE_ANON_KEY;

  if (!url) {
    throw new Error('COZE_SUPABASE_URL is not set. Please configure it in the platform environment variables.');
  }
  if (!anonKey) {
    throw new Error('COZE_SUPABASE_ANON_KEY is not set. Please configure it in the platform environment variables.');
  }

  supabaseInstance = createClient(url, anonKey, {
    db: {
      timeout: 60000,
    },
    auth: {
      autoRefreshToken: false,
      persistSession: false,
    },
  });

  return supabaseInstance;
}
