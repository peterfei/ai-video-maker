"""
视频生成工厂 - 主程序
整合所有模块，提供完整的视频生成流程
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import uuid

# 导入各模块
from config_loader import get_config
from utils import setup_logger, generate_filename, ensure_dir
from content_sources import TextSource, MaterialSource
from audio import TTSEngine, AudioMixer
from subtitle import SubtitleGenerator, SubtitleRenderer
from video_engine import VideoCompositor, VideoEffects
from tasks import TaskQueue, VideoTask, BatchProcessor, TaskStatus


class VideoFactory:
    """视频生成工厂主类"""

    def __init__(self, config_path: str = "config/default_config.yaml"):
        """
        初始化视频工厂

        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        self.config = get_config(config_path)
        self.logger = setup_logger("video_factory", self.config.get('batch.log_level', 'INFO'))

        # 初始化各模块
        self.text_source = TextSource(self.config.get('content_sources.text', {}))
        self.material_source = MaterialSource(self.config.get('content_sources.materials', {}))
        self.tts_engine = TTSEngine(self.config.get('tts', {}))
        self.audio_mixer = AudioMixer(self.config.get('music', {}))
        self.subtitle_generator = SubtitleGenerator(self.config.get('subtitle', {}))
        self.subtitle_renderer = SubtitleRenderer(self.config.get('subtitle', {}))
        self.video_compositor = VideoCompositor(self.config.get('video', {}))

        self.logger.info("视频生成工厂初始化完成")

    def generate_video(
        self,
        script_path: Optional[str] = None,
        script_text: Optional[str] = None,
        materials_dir: Optional[str] = None,
        output_path: Optional[str] = None,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成视频

        Args:
            script_path: 脚本文件路径
            script_text: 脚本文本
            materials_dir: 素材目录
            output_path: 输出路径
            title: 视频标题

        Returns:
            生成结果字典
        """
        self.logger.info("=" * 60)
        self.logger.info("开始生成视频")

        try:
            # 1. 加载脚本
            self.logger.info("步骤 1/7: 加载脚本")
            if script_path:
                script_segments = self.text_source.load_script(script_path)
                title = title or Path(script_path).stem
            elif script_text:
                script_segments = self.text_source.create_from_text(script_text)
                title = title or "untitled"
            else:
                raise ValueError("必须提供 script_path 或 script_text")

            self.logger.info(f"加载了 {len(script_segments)} 个脚本片段")

            # 2. 加载素材
            self.logger.info("步骤 2/7: 加载素材")
            if materials_dir:
                materials = self.material_source.load_materials(materials_dir)
                self.logger.info(f"加载了 {len(materials)} 个素材")
            else:
                materials = []
                self.logger.info("未提供素材目录，将生成纯背景视频")

            # 3. 生成语音
            self.logger.info("步骤 3/7: 生成语音")
            temp_dir = ensure_dir(Path("output/temp"))
            full_text = self.text_source.get_total_text(script_segments)

            audio_path = temp_dir / f"voice_{uuid.uuid4().hex[:8]}.mp3"
            self.tts_engine.text_to_speech(full_text, str(audio_path))
            audio_duration = self.tts_engine.get_audio_duration(str(audio_path))
            self.logger.info(f"语音生成完成，时长: {audio_duration:.2f}秒")

            # 4. 添加背景音乐
            self.logger.info("步骤 4/7: 添加背景音乐")
            if self.config.get('music.enabled', True):
                music_path = self.config.get('music.default_track')
                if music_path and Path(music_path).exists():
                    final_audio_path = temp_dir / f"final_audio_{uuid.uuid4().hex[:8]}.mp3"
                    self.audio_mixer.mix_voice_and_music(
                        str(audio_path),
                        music_path,
                        str(final_audio_path)
                    )
                    self.logger.info("背景音乐已添加")
                else:
                    final_audio_path = audio_path
                    self.logger.info("未找到背景音乐文件，使用纯语音")
            else:
                final_audio_path = audio_path
                self.logger.info("背景音乐已禁用")

            # 5. 生成字幕
            self.logger.info("步骤 5/7: 生成字幕")
            subtitle_segments = self.subtitle_generator.generate_from_text(
                full_text,
                audio_duration
            )
            self.logger.info(f"生成了 {len(subtitle_segments)} 个字幕片段")

            # 6. 创建视频
            self.logger.info("步骤 6/7: 创建视频")

            if materials:
                # 选择素材创建幻灯片
                selected_materials = self.material_source.select_materials(
                    count=max(5, len(script_segments)),
                    material_type='image'
                )

                if selected_materials:
                    image_paths = [m.path for m in selected_materials]
                    video_clip = self.video_compositor.create_slideshow(
                        images=image_paths,
                        audio_path=str(final_audio_path),
                        image_duration=self.config.get('templates.simple.image_duration', 5.0),
                        transition=self.config.get('templates.simple.transition', 'fade')
                    )
                else:
                    # 创建纯色背景视频
                    video_clip = self.video_compositor.create_background_video(audio_duration)
                    video_clip = video_clip.set_audio(
                        self.audio_mixer.audio_mixer.AudioFileClip(str(final_audio_path))
                    )
            else:
                # 创建纯色背景视频
                from moviepy.editor import AudioFileClip
                video_clip = self.video_compositor.create_background_video(audio_duration)
                audio_clip = AudioFileClip(str(final_audio_path))
                video_clip = video_clip.set_audio(audio_clip)

            # 7. 添加字幕
            self.logger.info("步骤 7/7: 渲染字幕")
            if self.config.get('subtitle.enabled', True):
                video_clip = self.subtitle_renderer.render_on_video(
                    video_clip,
                    subtitle_segments
                )
                self.logger.info("字幕已添加")

            # 8. 导出视频
            self.logger.info("导出视频...")
            if not output_path:
                output_dir = ensure_dir(Path(self.config.get('paths.output', 'output')))
                filename = generate_filename(
                    title,
                    self.config.get('export.filename_pattern', '{title}_{timestamp}'),
                    self.config.get('export.format', 'mp4')
                )
                output_path = output_dir / filename

            final_path = self.video_compositor.render_video(
                video_clip,
                str(output_path),
                preset=self._get_quality_preset()
            )

            self.logger.info(f"视频生成成功: {final_path}")
            self.logger.info("=" * 60)

            return {
                'success': True,
                'output_path': str(final_path),
                'duration': audio_duration,
                'subtitle_count': len(subtitle_segments),
                'title': title
            }

        except Exception as e:
            self.logger.error(f"视频生成失败: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())

            return {
                'success': False,
                'error': str(e)
            }

    def _get_quality_preset(self) -> str:
        """获取编码质量预设"""
        quality = self.config.get('export.quality', 'high')
        quality_map = {
            'ultra': 'slow',
            'high': 'medium',
            'medium': 'fast',
            'low': 'ultrafast'
        }
        return quality_map.get(quality, 'medium')

    def generate_from_task(self, task: VideoTask) -> Dict[str, Any]:
        """
        从任务生成视频

        Args:
            task: VideoTask对象

        Returns:
            生成结果
        """
        return self.generate_video(
            script_path=task.script_path,
            script_text=task.script_text,
            materials_dir=task.materials_dir,
            output_path=task.output_path
        )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="视频生成工厂")

    parser.add_argument('--script', '-s', type=str, help='脚本文件路径')
    parser.add_argument('--text', '-t', type=str, help='直接提供脚本文本')
    parser.add_argument('--materials', '-m', type=str, help='素材目录路径')
    parser.add_argument('--output', '-o', type=str, help='输出文件路径')
    parser.add_argument('--title', type=str, help='视频标题')
    parser.add_argument('--config', '-c', type=str, default='config/default_config.yaml',
                        help='配置文件路径')
    parser.add_argument('--batch', '-b', type=str, help='批量处理：脚本目录路径')

    args = parser.parse_args()

    # 创建视频工厂
    factory = VideoFactory(args.config)

    if args.batch:
        # 批量处理模式
        batch_process(factory, args.batch)
    else:
        # 单个视频生成
        if not args.script and not args.text:
            print("错误: 必须提供 --script 或 --text 参数")
            sys.exit(1)

        result = factory.generate_video(
            script_path=args.script,
            script_text=args.text,
            materials_dir=args.materials,
            output_path=args.output,
            title=args.title
        )

        if result['success']:
            print(f"\n✓ 视频生成成功!")
            print(f"  输出路径: {result['output_path']}")
            print(f"  时长: {result['duration']:.2f}秒")
            print(f"  字幕数: {result['subtitle_count']}")
        else:
            print(f"\n✗ 视频生成失败: {result['error']}")
            sys.exit(1)


def batch_process(factory: VideoFactory, scripts_dir: str):
    """
    批量处理

    Args:
        factory: VideoFactory实例
        scripts_dir: 脚本目录
    """
    scripts_path = Path(scripts_dir)

    if not scripts_path.exists():
        print(f"错误: 脚本目录不存在: {scripts_dir}")
        sys.exit(1)

    # 创建任务队列
    queue = TaskQueue(persistence_file="output/task_queue.json")

    # 扫描脚本文件
    script_files = list(scripts_path.glob("*.txt"))

    if not script_files:
        print(f"错误: 在 {scripts_dir} 中未找到 .txt 脚本文件")
        sys.exit(1)

    print(f"找到 {len(script_files)} 个脚本文件")

    # 创建任务
    for script_file in script_files:
        task = VideoTask(
            task_id=str(uuid.uuid4()),
            script_path=str(script_file),
            output_path=None  # 自动生成
        )
        queue.add_task(task)
        print(f"已添加任务: {script_file.name}")

    # 创建批处理器
    processor = BatchProcessor(
        task_queue=queue,
        config=factory.config.get('batch', {}),
        video_generator=factory.generate_from_task
    )

    # 处理任务
    print("\n开始批量处理...")
    stats = processor.process_all_pending()

    print(f"\n批量处理完成!")
    print(f"  总处理: {stats['total_processed']}")
    print(f"  成功: {stats['successful']}")
    print(f"  失败: {stats['failed']}")
    print(f"  耗时: {stats.get('duration_seconds', 0):.2f}秒")


if __name__ == "__main__":
    main()
