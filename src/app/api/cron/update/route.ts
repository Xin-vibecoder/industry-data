import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execAsync = promisify(exec);

// 鉴权：验证 cron secret
function validateAuth(request: Request): boolean {
  const authHeader = request.headers.get('authorization');
  const cronSecret = process.env.CRON_SECRET;
  
  // 如果没有配置 CRON_SECRET，拒绝访问
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

export async function GET(request: Request) {
  try {
    // 鉴权验证
    if (!validateAuth(request)) {
      return NextResponse.json(
        { error: 'Unauthorized', message: 'Invalid or missing authentication token' },
        { status: 401 }
      );
    }

    console.log('[Cron] Starting data update task...');
    
    // 获取项目根目录
    const projectRoot = process.env.COZE_WORKSPACE_PATH || process.cwd();
    const scriptPath = path.join(projectRoot, 'server', 'auto_update_data.py');
    
    // 执行 Python 更新脚本
    const { stdout, stderr } = await execAsync(
      `python3 "${scriptPath}"`,
      {
        timeout: 30 * 60 * 1000, // 30分钟超时
        cwd: projectRoot,
        env: {
          ...process.env,
          PYTHONUNBUFFERED: '1', // 实时输出
        }
      }
    );
    
    console.log('[Cron] Update script output:', stdout);
    if (stderr) {
      console.error('[Cron] Update script stderr:', stderr);
    }
    
    return NextResponse.json({
      success: true,
      message: 'Data update task completed',
      output: stdout.slice(-2000), // 返回最后2000字符的输出
      timestamp: new Date().toISOString(),
    });
    
  } catch (error) {
    console.error('[Cron] Update task failed:', error);
    
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    
    return NextResponse.json({
      success: false,
      error: errorMessage,
      timestamp: new Date().toISOString(),
    }, { status: 500 });
  }
}

// 也支持 POST 请求
export async function POST(request: Request) {
  return GET(request);
}
