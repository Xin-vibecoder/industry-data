import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';
import { existsSync } from 'fs';

const execAsync = promisify(exec);

// 鉴权：验证 cron secret
function validateAuth(request: Request): boolean {
  const authHeader = request.headers.get('authorization');
  const cronSecret = process.env.CRON_SECRET;
  
  if (!cronSecret) {
    console.error('CRON_SECRET is not configured');
    return false;
  }
  
  if (authHeader === `Bearer ${cronSecret}`) {
    return true;
  }
  
  const url = new URL(request.url);
  const tokenParam = url.searchParams.get('token');
  if (tokenParam === cronSecret) {
    return true;
  }
  
  return false;
}

// 检查 Python 环境
async function checkPythonEnvironment(): Promise<{ available: boolean; hasAkshare: boolean; message: string }> {
  try {
    // 检查 Python 是否可用
    await execAsync('python3 --version');
    
    // 检查 akshare 是否安装
    try {
      await execAsync('python3 -c "import akshare; print(akshare.__version__)"');
      return { available: true, hasAkshare: true, message: 'Python environment ready' };
    } catch {
      return { available: true, hasAkshare: false, message: 'Python available but akshare not installed' };
    }
  } catch {
    return { available: false, hasAkshare: false, message: 'Python not available in this environment' };
  }
}

export async function GET(request: Request) {
  const startTime = Date.now();
  
  try {
    // 鉴权验证
    if (!validateAuth(request)) {
      return NextResponse.json(
        { error: 'Unauthorized', message: 'Invalid or missing authentication token' },
        { status: 401 }
      );
    }

    console.log('[Cron] Starting data update task...');
    
    // 检查环境
    const envCheck = await checkPythonEnvironment();
    console.log('[Cron] Environment check:', envCheck);
    
    if (!envCheck.available) {
      return NextResponse.json({
        success: false,
        error: 'Python not available',
        message: 'This environment does not support Python. Please run the update script from a Python-enabled environment.',
        hint: 'You can run: python3 server/auto_update_data.py',
        environment: envCheck,
        timestamp: new Date().toISOString(),
      }, { status: 500 });
    }
    
    if (!envCheck.hasAkshare) {
      return NextResponse.json({
        success: false,
        error: 'akshare not installed',
        message: 'Python is available but akshare package is not installed.',
        hint: 'Run: pip install akshare pandas numpy',
        environment: envCheck,
        timestamp: new Date().toISOString(),
      }, { status: 500 });
    }
    
    // 获取项目根目录
    const projectRoot = process.env.COZE_WORKSPACE_PATH || process.cwd();
    const scriptPath = path.join(projectRoot, 'server', 'auto_update_data.py');
    
    // 检查脚本是否存在
    if (!existsSync(scriptPath)) {
      return NextResponse.json({
        success: false,
        error: 'Update script not found',
        message: `Script not found: ${scriptPath}`,
        timestamp: new Date().toISOString(),
      }, { status: 500 });
    }
    
    // 执行 Python 更新脚本
    const { stdout, stderr } = await execAsync(
      `python3 "${scriptPath}"`,
      {
        timeout: 30 * 60 * 1000, // 30分钟超时
        cwd: projectRoot,
        env: {
          ...process.env,
          PYTHONUNBUFFERED: '1',
        }
      }
    );
    
    const duration = Date.now() - startTime;
    console.log(`[Cron] Update completed in ${duration}ms`);
    
    return NextResponse.json({
      success: true,
      message: 'Data update task completed',
      duration: `${Math.round(duration / 1000)}s`,
      output: stdout.slice(-2000),
      timestamp: new Date().toISOString(),
    });
    
  } catch (error) {
    const duration = Date.now() - startTime;
    console.error(`[Cron] Update failed after ${duration}ms:`, error);
    
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    
    return NextResponse.json({
      success: false,
      error: errorMessage,
      duration: `${Math.round(duration / 1000)}s`,
      timestamp: new Date().toISOString(),
    }, { status: 500 });
  }
}

export async function POST(request: Request) {
  return GET(request);
}
