import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const incrementalDays = body.incrementalDays || 5;

    // 执行Python脚本进行增量更新
    const scriptPath = `${process.cwd()}/server/calculate_rankings.py`;
    const { stdout, stderr } = await execAsync(`python3 ${scriptPath} --incremental ${incrementalDays}`);

    if (stderr && !stderr.includes('✓')) {
      console.error('Update error:', stderr);
      return NextResponse.json(
        { error: 'Failed to update rankings', details: stderr },
        { status: 500 }
      );
    }

    return NextResponse.json({
      success: true,
      message: `Rankings updated for last ${incrementalDays} days`,
      output: stdout
    });
  } catch (error) {
    console.error('Update rankings error:', error);
    return NextResponse.json(
      { error: 'Failed to update rankings' },
      { status: 500 }
    );
  }
}
