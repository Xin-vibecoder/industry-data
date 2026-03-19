import { NextResponse } from 'next/server';
import { runIncrementalUpdate } from '@/lib/data-updater';

/**
 * 鉴权：验证 cron secret
 */
function validateAuth(request: Request): boolean {
  const authHeader = request.headers.get('authorization');
  const cronSecret = process.env.CRON_SECRET;
  
  if (!cronSecret) {
    console.error('CRON_SECRET is not configured');
    return false;
  }
  
  // 验证 Authorization: Bearer <token>
  if (authHeader === `Bearer ${cronSecret}`) {
    return true;
  }
  
  // 也支持 query parameter 方式
  const url = new URL(request.url);
  const tokenParam = url.searchParams.get('token');
  if (tokenParam === cronSecret) {
    return true;
  }
  
  return false;
}

/**
 * 增量更新 API
 * GET /api/cron/update?token=xxx
 * 或
 * GET /api/cron/update (Header: Authorization: Bearer xxx)
 */
export async function GET(request: Request) {
  const startTime = Date.now();
  
  try {
    // 鉴权验证
    if (!validateAuth(request)) {
      return NextResponse.json(
        { 
          success: false,
          error: 'Unauthorized', 
          message: 'Invalid or missing authentication token' 
        },
        { status: 401 }
      );
    }

    console.log('[Cron API] Starting incremental update...');
    
    // 执行增量更新
    const result = await runIncrementalUpdate();
    
    return NextResponse.json({
      success: result.success,
      message: result.message,
      stats: {
        sectorsUpdated: result.sectorsUpdated,
        recordsInserted: result.recordsInserted,
        rankingsUpdated: result.rankingsUpdated,
        errors: result.errors.length,
      },
      errors: result.errors.length > 0 ? result.errors : undefined,
      duration: `${Math.round(result.duration / 1000)}s`,
      timestamp: new Date().toISOString(),
    });
    
  } catch (error) {
    const duration = Date.now() - startTime;
    console.error(`[Cron API] Update failed after ${duration}ms:`, error);
    
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    
    return NextResponse.json({
      success: false,
      error: errorMessage,
      duration: `${Math.round(duration / 1000)}s`,
      timestamp: new Date().toISOString(),
    }, { status: 500 });
  }
}

// 也支持 POST 请求
export async function POST(request: Request) {
  return GET(request);
}
