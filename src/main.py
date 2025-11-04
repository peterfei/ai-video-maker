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
from content_sources import TextSource, MaterialSource, AutoMaterialManager
from audio import TTSEngine, AudioMixer, STTEngine, MusicLibrary
from subtitle import SubtitleGenerator, SubtitleRenderer, STTSubtitleGenerator
from video_engine import VideoCompositor, VideoEffects
from video_engine.gpu_accelerator import GPUVideoAccelerator
from video_engine.gpu_effects import GPUEffectsProcessor
from tasks import TaskQueue, VideoTask, BatchProcessor, TaskStatus
from tasks.parallel_batch_processor import ParallelBatchProcessor


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

        # 初始化 STT 相关模块
        self.stt_enabled = self.config.get('stt.enabled', False)
        if self.stt_enabled:
            self.stt_engine = STTEngine(self.config.get('stt', {}))
            self.stt_subtitle_generator = STTSubtitleGenerator(self.config.get('subtitle', {}))
            self.logger.info("STT 引擎已启用")
        else:
            self.stt_engine = None
            self.stt_subtitle_generator = None

        # 初始化自动素材管理器（如果启用）
        self.auto_material_enabled = self.config.get('auto_materials.enabled', False)
        if self.auto_material_enabled:
            self.auto_material_manager = AutoMaterialManager(self.config.get('auto_materials', {}))
            self.logger.info("自动素材管理器已启用")

        # 初始化音乐库（如果启用）
        self.music_enabled = self.config.get('music.enabled', False)
        if self.music_enabled:
            self.music_library = MusicLibrary(self.config.get('music', {}))
            self.logger.info("智能背景音乐库已启用")
        else:
            self.music_library = None

        # 初始化GPU加速器和效果处理器
        self.gpu_accelerator = GPUVideoAccelerator(self.config.get('performance', {}).get('gpu', {}))
        self.gpu_effects = GPUEffectsProcessor(self.gpu_accelerator)

        if self.gpu_accelerator.is_gpu_available():
            gpu_info = self.gpu_accelerator.get_gpu_info()
            self.logger.info(f"GPU加速已启用: {gpu_info['name']} ({gpu_info['memory_total_gb']:.1f}GB)")
        else:
            self.logger.info("GPU不可用，使用CPU处理")

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
                # 优先使用指定的素材目录
                materials = self.material_source.load_materials(materials_dir)
                self.logger.info(f"从指定目录 {materials_dir} 加载了 {len(materials)} 个素材")
                # 记录前几个素材路径用于调试
                for i, material in enumerate(materials[:3]):
                    self.logger.debug(f"  素材 {i+1}: {material.path}")
            elif self.auto_material_enabled:
                # 使用自动素材管理器
                self.logger.info("使用自动素材管理器获取素材")
                material_paths = self.auto_material_manager.get_materials_for_script(
                    script_segments,
                    materials_per_segment=self.config.get('auto_materials.materials_per_segment', 1)
                )
                # 转换路径为Material对象列表
                materials = [{'path': p} for p in material_paths] if material_paths else []
                self.logger.info(f"自动获取了 {len(materials)} 个素材")
            else:
                materials = []
                self.logger.info("未提供素材目录，将生成纯背景视频")

            # 3. 生成语音（分段生成以获取精确时长）
            self.logger.info("步骤 3/7: 生成语音（分段模式）")
            temp_dir = ensure_dir(Path("output/temp"))

            # 获取所有句子
            sentences = []
            for seg in script_segments:
                # 将每个脚本片段的文本按句子分割
                seg_sentences = self.subtitle_generator._split_into_sentences(seg.text)
                sentences.extend(seg_sentences)

            self.logger.info(f"共分割为 {len(sentences)} 个句子")

            # 为每个句子生成音频，并获取实际时长
            segment_dir = temp_dir / f"segments_{uuid.uuid4().hex[:8]}"
            audio_paths, audio_durations = self.tts_engine.generate_segments(
                sentences,
                str(segment_dir)
            )

            self.logger.info(f"生成了 {len(audio_paths)} 个音频片段")

            # 拼接所有音频片段
            audio_path = temp_dir / f"voice_{uuid.uuid4().hex[:8]}.mp3"
            self.audio_mixer.concatenate_audio_files(
                audio_paths,
                str(audio_path),
                silence_duration=0.0  # 不插入静音
            )

            audio_duration = sum(audio_durations)
            self.logger.info(f"语音生成完成，总时长: {audio_duration:.2f}秒")

            # 4. 添加背景音乐
            self.logger.info("步骤 4/7: 添加背景音乐")
            if self.config.get('music.basic_enabled', True):
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

            # 5. 生成字幕（基于实际音频时长）
            self.logger.info("步骤 5/7: 生成字幕（精确同步模式）")
            subtitle_segments = self.subtitle_generator.generate_from_segments(
                sentences,
                audio_durations
            )
            self.logger.info(f"生成了 {len(subtitle_segments)} 个字幕片段（精确同步）")

            # 6. 创建视频
            self.logger.info("步骤 6/7: 创建视频")

            if materials:
                # 处理素材路径
                if isinstance(materials[0], dict) and 'path' in materials[0]:
                    # 来自自动素材管理器的路径列表
                    image_paths = [m['path'] for m in materials]
                elif hasattr(materials[0], 'path'):
                    # 直接使用从指定目录加载的Material对象
                    # 按脚本片段数量选择素材，或使用全部可用素材
                    material_count = max(len(script_segments), len(materials))
                    if len(materials) >= material_count:
                        selected_materials = materials[:material_count]
                    else:
                        # 如果素材不足，循环重复使用
                        selected_materials = (materials * (material_count // len(materials) + 1))[:material_count]
                    image_paths = [m.path for m in selected_materials]
                    self.logger.info(f"使用指定目录的 {len(selected_materials)} 个素材")
                else:
                    # 降级方案：来自material_source的Material对象
                    selected_materials = self.material_source.select_materials(
                        count=max(5, len(script_segments)),
                        material_type='image'
                    )
                    image_paths = [m.path for m in selected_materials] if selected_materials else []

                if image_paths:
                    # 使用GPU加速的幻灯片制作（如果可用）
                    if self.gpu_accelerator.is_gpu_available():
                        self.logger.info("使用GPU加速幻灯片制作")
                        video_clip = self.gpu_effects.create_slideshow_gpu(
                            images=image_paths,
                            audio_path=str(final_audio_path),
                            image_duration=self.config.get('templates.simple.image_duration', 5.0),
                            transition=self.config.get('templates.simple.transition', 'fade'),
                            transition_duration=self.config.get('templates.simple.transition_duration', 0.5)
                        )
                    else:
                        video_clip = self.video_compositor.create_slideshow(
                            images=image_paths,
                            audio_path=str(final_audio_path),
                            image_duration=self.config.get('templates.simple.image_duration', 5.0),
                            transition=self.config.get('templates.simple.transition', 'fade'),
                            transition_duration=self.config.get('templates.simple.transition_duration', 0.5)
                        )
                else:
                    # 创建纯色背景视频
                    from moviepy.editor import AudioFileClip
                    video_clip = self.video_compositor.create_background_video(audio_duration)
                    audio_clip = AudioFileClip(str(final_audio_path))
                    video_clip = video_clip.set_audio(audio_clip)
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

    async def generate_video_with_music(
        self,
        text: str,
        output_path: Optional[str] = None,
        title: Optional[str] = None,
        materials_dir: Optional[str] = None,
        auto_music: bool = True
    ) -> Dict[str, Any]:
        """
        生成带智能背景音乐的视频

        Args:
            text: 视频文本内容
            output_path: 输出视频路径
            title: 视频标题
            materials_dir: 素材目录路径
            auto_music: 是否自动选择背景音乐

        Returns:
            生成结果字典
        """
        self.logger.info("=" * 60)
        self.logger.info("开始生成带智能背景音乐的视频")

        try:
            # 检查音乐功能是否启用
            if not self.music_enabled or not self.music_library:
                self.logger.warning("智能背景音乐功能未启用，将使用标准视频生成")
                # 降级到标准视频生成
                return self.generate_video(
                    script_text=text,
                    materials_dir=materials_dir,
                    output_path=output_path,
                    title=title
                )

            # 1. 加载脚本
            self.logger.info("步骤 1/8: 加载脚本")
            script_segments = self.text_source.create_from_text(text)
            title = title or "auto_music_video"
            self.logger.info(f"加载了 {len(script_segments)} 个脚本片段")

            # 2. 智能选择背景音乐
            self.logger.info("步骤 2/8: 智能选择背景音乐")
            full_text = " ".join(seg.text for seg in script_segments)

            # 估算视频时长（简单估算）
            estimated_duration = len(full_text.split()) * 0.5  # 假设每秒0.5个词

            music_recommendation = None
            if auto_music:
                music_recommendation = await self.music_library.get_music_for_content(
                    full_text, estimated_duration
                )

                if music_recommendation:
                    self.logger.info(f"选择了背景音乐: {music_recommendation.title} ({music_recommendation.source})")
                else:
                    self.logger.warning("未找到合适的背景音乐，将使用默认背景音乐")
            else:
                self.logger.info("自动音乐选择已禁用")

            # 3. 加载素材
            self.logger.info("步骤 3/8: 加载素材")
            if materials_dir:
                # 优先使用指定的素材目录
                materials = self.material_source.load_materials(materials_dir)
                self.logger.info(f"从指定目录 {materials_dir} 加载了 {len(materials)} 个素材")
            elif self.auto_material_enabled:
                # 使用自动素材管理器
                self.logger.info("使用自动素材管理器获取素材")
                material_paths = self.auto_material_manager.get_materials_for_script(
                    script_segments,
                    materials_per_segment=self.config.get('auto_materials.materials_per_segment', 1)
                )
                materials = [{'path': p} for p in material_paths] if material_paths else []
                self.logger.info(f"自动获取了 {len(materials)} 个素材")
            else:
                materials = []
                self.logger.info("未提供素材目录，将生成纯背景视频")

            # 4. 生成语音
            self.logger.info("步骤 4/8: 生成语音")
            temp_dir = ensure_dir(Path("output/temp"))

            # 获取所有句子
            sentences = []
            for seg in script_segments:
                seg_sentences = self.subtitle_generator._split_into_sentences(seg.text)
                sentences.extend(seg_sentences)

            self.logger.info(f"共分割为 {len(sentences)} 个句子")

            # 生成音频片段
            segment_dir = temp_dir / f"segments_{uuid.uuid4().hex[:8]}"
            audio_paths, audio_durations = self.tts_engine.generate_segments(
                sentences,
                str(segment_dir)
            )

            self.logger.info(f"生成了 {len(audio_paths)} 个音频片段")

            # 拼接音频
            voice_audio_path = temp_dir / f"voice_{uuid.uuid4().hex[:8]}.mp3"
            self.audio_mixer.concatenate_audio_files(
                audio_paths,
                str(voice_audio_path),
                silence_duration=0.0
            )

            audio_duration = sum(audio_durations)
            self.logger.info(f"语音生成完成，总时长: {audio_duration:.2f}秒")

            # 5. 处理背景音乐
            self.logger.info("步骤 5/8: 处理背景音乐")
            if music_recommendation and music_recommendation.local_path:
                # 使用智能选择的音乐
                music_path = music_recommendation.local_path
                final_audio_path = temp_dir / f"final_audio_{uuid.uuid4().hex[:8]}.mp3"
                self.audio_mixer.mix_voice_and_music(
                    str(voice_audio_path),
                    music_path,
                    str(final_audio_path)
                )
                self.logger.info("智能背景音乐已混合")
            else:
                # 使用默认背景音乐或纯语音
                if self.config.get('music.basic_enabled', True):
                    default_music = self.config.get('music.default_track')
                    if default_music and Path(default_music).exists():
                        final_audio_path = temp_dir / f"final_audio_{uuid.uuid4().hex[:8]}.mp3"
                        self.audio_mixer.mix_voice_and_music(
                            str(voice_audio_path),
                            default_music,
                            str(final_audio_path)
                        )
                        self.logger.info("默认背景音乐已添加")
                    else:
                        final_audio_path = voice_audio_path
                        self.logger.info("未找到背景音乐文件，使用纯语音")
                else:
                    final_audio_path = voice_audio_path
                    self.logger.info("背景音乐已禁用")

            # 6. 生成字幕
            self.logger.info("步骤 6/8: 生成字幕")
            subtitle_segments = self.subtitle_generator.generate_from_segments(
                sentences,
                audio_durations
            )
            self.logger.info(f"生成了 {len(subtitle_segments)} 个字幕片段")

            # 7. 创建视频
            self.logger.info("步骤 7/8: 创建视频")

            if materials:
                # 处理素材路径
                if isinstance(materials[0], dict) and 'path' in materials[0]:
                    image_paths = [m['path'] for m in materials]
                else:
                    selected_materials = self.material_source.select_materials(
                        count=max(5, len(script_segments)),
                        material_type='image'
                    )
                    image_paths = [m.path for m in selected_materials] if selected_materials else []

                if image_paths:
                    # 使用GPU加速的幻灯片制作（如果可用）
                    if self.gpu_accelerator.is_gpu_available():
                        self.logger.info("使用GPU加速幻灯片制作")
                        video_clip = self.gpu_effects.create_slideshow_gpu(
                            images=image_paths,
                            audio_path=str(final_audio_path),
                            image_duration=self.config.get('templates.simple.image_duration', 5.0),
                            transition=self.config.get('templates.simple.transition', 'fade'),
                            transition_duration=self.config.get('templates.simple.transition_duration', 0.5)
                        )
                    else:
                        video_clip = self.video_compositor.create_slideshow(
                            images=image_paths,
                            audio_path=str(final_audio_path),
                            image_duration=self.config.get('templates.simple.image_duration', 5.0),
                            transition=self.config.get('templates.simple.transition', 'fade'),
                            transition_duration=self.config.get('templates.simple.transition_duration', 0.5)
                        )
                else:
                    # 创建纯色背景视频
                    from moviepy.editor import AudioFileClip
                    video_clip = self.video_compositor.create_background_video(audio_duration)
                    audio_clip = AudioFileClip(str(final_audio_path))
                    video_clip = video_clip.set_audio(audio_clip)
            else:
                # 创建纯色背景视频
                from moviepy.editor import AudioFileClip
                video_clip = self.video_compositor.create_background_video(audio_duration)
                audio_clip = AudioFileClip(str(final_audio_path))
                video_clip = video_clip.set_audio(audio_clip)

            # 8. 添加字幕并导出
            self.logger.info("步骤 8/8: 渲染字幕并导出")
            if self.config.get('subtitle.enabled', True):
                video_clip = self.subtitle_renderer.render_on_video(
                    video_clip,
                    subtitle_segments
                )
                self.logger.info("字幕已添加")

            # 导出视频
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

            self.logger.info(f"智能背景音乐视频生成成功: {final_path}")
            self.logger.info("=" * 60)

            return {
                'success': True,
                'output_path': str(final_path),
                'duration': audio_duration,
                'subtitle_count': len(subtitle_segments),
                'title': title,
                'music_used': music_recommendation.title if music_recommendation else None,
                'music_source': music_recommendation.source if music_recommendation else None,
                'music_copyright_status': music_recommendation.copyright_status.value if music_recommendation else None
            }

        except Exception as e:
            self.logger.error(f"智能背景音乐视频生成失败: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())

            return {
                'success': False,
                'error': str(e)
            }

    def generate_video_from_audio(
        self,
        audio_path: str,
        output_path: Optional[str] = None,
        title: Optional[str] = None,
        materials_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        从音频文件生成带字幕的视频

        Args:
            audio_path: 音频文件路径
            output_path: 输出视频路径
            title: 视频标题
            materials_dir: 素材目录路径

        Returns:
            生成结果字典
        """
        self.logger.info("=" * 60)
        self.logger.info("开始从音频生成带字幕的视频")

        try:
            # 检查 STT 功能是否启用
            if not self.stt_enabled or not self.stt_engine or not self.stt_subtitle_generator:
                raise RuntimeError("STT 功能未启用，请在配置中设置 stt.enabled=true")

            # 1. 验证音频文件
            self.logger.info("步骤 1/6: 验证音频文件")
            audio_path = Path(audio_path)
            if not audio_path.exists():
                raise FileNotFoundError(f"音频文件不存在: {audio_path}")

            if not self.stt_engine.validate_audio_format(str(audio_path)):
                raise ValueError(f"不支持的音频格式: {audio_path.suffix}")

            # 2. 加载素材（如果提供）
            self.logger.info("步骤 2/6: 加载素材")
            materials = []
            if materials_dir:
                materials = self.material_source.load_materials(materials_dir)
                self.logger.info(f"加载了 {len(materials)} 个素材")
            else:
                self.logger.info("未提供素材目录，将生成纯背景视频")

            # 3. STT 语音转文字
            self.logger.info("步骤 3/6: 执行语音转文字")
            stt_result = self.stt_engine.transcribe(str(audio_path))

            if not stt_result.segments:
                raise RuntimeError("STT 转录失败，未识别到任何语音内容")

            self.logger.info(
                f"语音转文字完成: {len(stt_result.segments)} 个片段，"
                ".2f"
                ".2f"
            )

            # 4. 生成字幕
            self.logger.info("步骤 4/6: 生成字幕")
            subtitle_segments = self.stt_subtitle_generator.generate_from_stt(stt_result)
            self.logger.info(f"字幕生成完成: {len(subtitle_segments)} 个字幕片段")

            # 5. 创建视频
            self.logger.info("步骤 5/6: 创建视频")

            # 确定音频时长
            audio_duration = stt_result.duration

            if materials:
                # 处理素材路径
                if isinstance(materials[0], dict) and 'path' in materials[0]:
                    # 来自自动素材管理器的路径列表
                    image_paths = [m['path'] for m in materials]
                else:
                    # 来自material_source的Material对象
                    selected_materials = self.material_source.select_materials(
                        count=max(5, len(subtitle_segments)),  # 基于字幕数量选择素材
                        material_type='image'
                    )
                    image_paths = [m.path for m in selected_materials] if selected_materials else []

                if image_paths:
                    # 使用GPU加速的幻灯片制作（如果可用）
                    if self.gpu_accelerator.is_gpu_available():
                        self.logger.info("使用GPU加速幻灯片制作")
                        video_clip = self.gpu_effects.create_slideshow_gpu(
                            images=image_paths,
                            audio_path=str(audio_path),
                            image_duration=self.config.get('templates.simple.image_duration', 5.0),
                            transition=self.config.get('templates.simple.transition', 'fade'),
                            transition_duration=self.config.get('templates.simple.transition_duration', 0.5)
                        )
                    else:
                        video_clip = self.video_compositor.create_slideshow(
                            images=image_paths,
                            audio_path=str(audio_path),
                            image_duration=self.config.get('templates.simple.image_duration', 5.0),
                            transition=self.config.get('templates.simple.transition', 'fade'),
                            transition_duration=self.config.get('templates.simple.transition_duration', 0.5)
                        )
                else:
                    # 创建纯色背景视频
                    from moviepy.editor import AudioFileClip
                    video_clip = self.video_compositor.create_background_video(audio_duration)
                    audio_clip = AudioFileClip(str(audio_path))
                    video_clip = video_clip.set_audio(audio_clip)
            else:
                # 创建纯色背景视频
                from moviepy.editor import AudioFileClip
                video_clip = self.video_compositor.create_background_video(audio_duration)
                audio_clip = AudioFileClip(str(audio_path))
                video_clip = video_clip.set_audio(audio_clip)

            # 6. 添加字幕
            self.logger.info("步骤 6/6: 渲染字幕")
            if self.config.get('subtitle.enabled', True) and subtitle_segments:
                video_clip = self.subtitle_renderer.render_on_video(
                    video_clip,
                    subtitle_segments
                )
                self.logger.info("字幕已添加")

            # 7. 导出视频
            self.logger.info("导出视频...")
            if not output_path:
                output_dir = ensure_dir(Path(self.config.get('paths.output', 'output')))
                title = title or audio_path.stem
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
                'stt_segments': len(stt_result.segments),
                'language': stt_result.language,
                'title': title or audio_path.stem
            }

        except Exception as e:
            self.logger.error(f"音频视频生成失败: {str(e)}")
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
    parser.add_argument('--audio', '-a', type=str, help='音频文件路径（用于生成字幕的语音文件）')
    parser.add_argument('--materials', '-m', type=str, help='素材目录路径')
    parser.add_argument('--output', '-o', type=str, help='输出文件路径')
    parser.add_argument('--title', type=str, help='视频标题')
    parser.add_argument('--config', '-c', type=str, default='config/default_config.yaml',
                         help='配置文件路径')
    parser.add_argument('--batch', '-b', type=str, help='批量处理：脚本目录路径')

    # 音乐相关选项
    parser.add_argument('--auto-music', action='store_true', default=None,
                         help='启用智能背景音乐选择（默认启用）')
    parser.add_argument('--no-music', action='store_true',
                         help='禁用智能背景音乐选择')
    parser.add_argument('--music-genre', type=str,
                         help='指定音乐类型（ambient, electronic, classical, jazz）')
    parser.add_argument('--music-mood', type=str,
                         help='指定音乐情绪（calm, inspiring, energetic）')

    # 字体管理选项
    parser.add_argument('--font-manager', action='store_true', help='启动字体管理器界面')
    parser.add_argument('--add-font', type=str, help='添加自定义字体文件')
    parser.add_argument('--preview-font', type=str, help='预览字体效果')
    parser.add_argument('--list-fonts', action='store_true', help='列出所有可用字体')

    args = parser.parse_args()

    # 创建视频工厂
    factory = VideoFactory(args.config)

    # 处理字体管理命令
    if args.font_manager or args.add_font or args.preview_font or args.list_fonts:
        handle_font_commands(factory, args)
        return

    if args.batch:
        # 批量处理模式
        batch_process(factory, args.batch)
    else:
        # 检查输入参数
        input_count = sum([bool(args.script), bool(args.text), bool(args.audio)])
        if input_count == 0:
            print("错误: 必须提供以下参数之一:")
            print("  --script (-s): 脚本文件路径")
            print("  --text (-t): 直接提供脚本文本")
            print("  --audio (-a): 音频文件路径（用于生成字幕）")
            sys.exit(1)
        elif input_count > 1:
            print("错误: 不能同时提供多个输入源 (--script, --text, --audio)")
            sys.exit(1)

        # 根据输入类型调用相应方法
        if args.audio:
            # 音频输入模式
            result = factory.generate_video_from_audio(
                audio_path=args.audio,
                output_path=args.output,
                title=args.title,
                materials_dir=args.materials
            )

            if result['success']:
                print(f"\n✓ 音频字幕视频生成成功!")
                print(f"  输出路径: {result['output_path']}")
                print(f"  时长: {result['duration']:.2f}秒")
                print(f"  字幕数: {result['subtitle_count']}")
                print(f"  STT片段数: {result['stt_segments']}")
                print(f"  识别语言: {result['language']}")
            else:
                print(f"\n✗ 音频字幕视频生成失败: {result['error']}")
                sys.exit(1)
        else:
            # 处理音乐选项
            auto_music = factory.config.get('music.auto_music', True)  # 从配置读取默认值
            if args.no_music:
                auto_music = False
            elif args.auto_music is not None:
                auto_music = args.auto_music

            # 检查是否使用智能音乐功能
            use_smart_music = factory.music_enabled and auto_music

            if use_smart_music:
                # 使用智能背景音乐功能
                import asyncio

                # 处理输入文本
                input_text = args.text
                if args.script:
                    # 从脚本文件读取文本
                    script_path = Path(args.script)
                    if not script_path.exists():
                        print(f"错误: 脚本文件不存在: {args.script}")
                        sys.exit(1)
                    try:
                        input_text = script_path.read_text(encoding='utf-8')
                        if not args.title:
                            args.title = script_path.stem
                    except Exception as e:
                        print(f"错误: 读取脚本文件失败: {e}")
                        sys.exit(1)

                if not input_text:
                    print("错误: 必须提供文本内容 (--text) 或脚本文件 (--script)")
                    sys.exit(1)

                result = asyncio.run(factory.generate_video_with_music(
                    text=input_text,
                    output_path=args.output,
                    title=args.title,
                    materials_dir=args.materials,
                    auto_music=auto_music
                ))

                if result['success']:
                    print(f"\n✓ 智能背景音乐视频生成成功!")
                    print(f"  输出路径: {result['output_path']}")
                    print(f"  时长: {result['duration']:.2f}秒")
                    print(f"  字幕数: {result['subtitle_count']}")
                    if result.get('music_used'):
                        print(f"  背景音乐: {result['music_used']}")
                        print(f"  音乐来源: {result['music_source']}")
                        print(f"  版权状态: {result['music_copyright_status']}")
                else:
                    print(f"\n✗ 智能背景音乐视频生成失败: {result['error']}")
                    sys.exit(1)
            else:
                # 使用原有视频生成功能
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

    # 检查是否启用性能优化
    perf_config = factory.config.get('performance', {})
    threading_enabled = perf_config.get('threading', {}).get('enabled', False)

    if threading_enabled:
        # 使用并行批处理器
        print("⚡ 使用并行批处理器（多线程 + GPU加速）")
        processor = ParallelBatchProcessor(
            task_queue=queue,
            config=perf_config,
            video_generator=factory.generate_from_task
        )
    else:
        # 使用传统批处理器
        print("🔄 使用传统批处理器")
        processor = BatchProcessor(
            task_queue=queue,
            config=factory.config.get('batch', {}),
            video_generator=factory.generate_from_task
        )

    # 处理任务
    print("\n开始批量处理...")
    if threading_enabled:
        result = processor.process_batch()
        stats = {
            'total_processed': result.total_tasks,
            'successful': result.successful_tasks,
            'failed': result.failed_tasks,
            'duration_seconds': result.total_duration,
            'throughput': result.throughput,
            'peak_memory_usage': result.peak_memory_usage
        }
    else:
        stats = processor.process_all_pending()

    print(f"\n批量处理完成!")
    print(f"  总处理: {stats['total_processed']}")
    print(f"  成功: {stats['successful']}")
    print(f"  失败: {stats['failed']}")
    print(f"  耗时: {stats.get('duration_seconds', 0):.2f}秒")

    # 显示额外性能信息
    if threading_enabled:
        print(f"  吞吐量: {stats.get('throughput', 0):.2f} tasks/秒")
        print(f"  峰值内存: {stats.get('peak_memory_usage', 0)} MB")

    # 关闭并行处理器
    if threading_enabled:
        processor.shutdown()


def handle_font_commands(factory: VideoFactory, args):
    """
    处理字体管理相关命令

    Args:
        factory: VideoFactory实例
        args: 命令行参数
    """
    font_manager = factory.subtitle_renderer.font_manager

    if args.list_fonts:
        # 列出所有可用字体
        print("🔤 可用字体列表:")
        print("=" * 60)

        try:
            fonts_info = font_manager.get_available_fonts_info()
            chinese_fonts = [f for f in fonts_info if f.get('supports_chinese', False)]

            if chinese_fonts:
                count = len(chinese_fonts)
                print("📝 支持中文的字体 ({} 个):".format(count))
                for i, font in enumerate(chinese_fonts[:20], 1):  # 显示前20个
                    status = "✓" if font['exists'] else "✗"
                    source = font.get('source', 'unknown')
                    print("  {:2d}. {} {} [{}]".format(i, status, font['name'], source))
            else:
                print("❌ 未找到支持中文的字体")

            total_fonts = len(fonts_info)
            chinese_count = len(chinese_fonts)
            print("\n📊 总计: {} 个字体，其中 {} 个支持中文".format(total_fonts, chinese_count))

        except Exception as e:
            print("❌ 获取字体信息失败: {}".format(str(e)))

    elif args.add_font:
        # 添加自定义字体
        print("📥 添加自定义字体: {}".format(args.add_font))

        try:
            if font_manager.add_custom_font(args.add_font):
                print("✅ 字体添加成功！")
            else:
                print("❌ 字体添加失败")
                sys.exit(1)
        except Exception as e:
            print("❌ 字体添加出错: {}".format(str(e)))
            sys.exit(1)

    elif args.preview_font:
        # 预览字体
        print("👁️ 预览字体: {}".format(args.preview_font))

        try:
            preview_path = font_manager.preview_font(args.preview_font)
            if preview_path:
                print("✅ 预览图片生成: {}".format(preview_path))
                print("💡 提示: 预览图片已保存，可手动查看")
            else:
                print("❌ 字体预览生成失败")
                sys.exit(1)
        except Exception as e:
            print("❌ 字体预览出错: {}".format(str(e)))
            sys.exit(1)

    elif args.font_manager:
        # 启动字体管理器界面
        print("🎨 字体管理器")
        print("=" * 40)

        try:
            while True:
                print("\n选择操作:")
                print("1. 列出所有字体")
                print("2. 添加自定义字体")
                print("3. 预览字体")
                print("4. 测试字体兼容性")
                print("5. 退出")

                choice = input("\n请选择 (1-5): ").strip()

                if choice == '1':
                    # 列出字体
                    fonts_info = font_manager.get_available_fonts_info()
                    chinese_fonts = [f for f in fonts_info if f.get('supports_chinese', False)]

                    count = len(chinese_fonts)
                    print("\n支持中文的字体 ({} 个):".format(count))
                    for i, font in enumerate(chinese_fonts[:10], 1):
                        status = "✓" if font['exists'] else "✗"
                        source = font.get('source', 'unknown')
                        print("  {:2d}. {} {} [{}]".format(i, status, font['name'], source))

                    if len(chinese_fonts) > 10:
                        remaining = len(chinese_fonts) - 10
                        print("  ... 还有 {} 个字体".format(remaining))

                elif choice == '2':
                    # 添加字体
                    font_path = input("输入字体文件路径: ").strip()
                    if font_path:
                        if font_manager.add_custom_font(font_path):
                            print("✅ 字体添加成功！")
                        else:
                            print("❌ 字体添加失败")
                    else:
                        print("❌ 字体路径不能为空")

                elif choice == '3':
                    # 预览字体
                    font_name = input("输入字体名称或路径: ").strip()
                    if font_name:
                        preview_path = font_manager.preview_font(font_name)
                        if preview_path:
                            print("✅ 预览图片: {}".format(preview_path))
                        else:
                            print("❌ 预览生成失败")
                    else:
                        print("❌ 字体名称不能为空")

                elif choice == '4':
                    # 测试兼容性
                    font_name = input("输入字体名称或路径: ").strip()
                    if font_name:
                        results = font_manager.test_font_compatibility(font_name)
                        print("\n字体兼容性测试结果 ({}):".format(font_name))
                        for test, result in results.items():
                            status = "✅" if result else "❌"
                            print("  {}: {}".format(test, status))
                    else:
                        print("❌ 字体名称不能为空")

                elif choice == '5':
                    # 退出
                    print("👋 再见！")
                    break

                else:
                    print("❌ 无效选择，请重新输入")

        except KeyboardInterrupt:
            print("\n👋 再见！")
        except Exception as e:
            print("❌ 字体管理器出错: {}".format(str(e)))

if __name__ == "__main__":
    main()
