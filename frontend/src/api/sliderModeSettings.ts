/**
 * 滑块滑动方式设置接口
 */
import { put } from '@/utils/request'
import type { ApiResponse } from '@/types'

const SLIDER_MODE_URL = '/system-settings/captcha.slider_mode'
const SLIDER_MODES = ['browser', 'real_mouse'] as const
export type SliderMode = (typeof SLIDER_MODES)[number]

export const normalizeSliderMode = (value: unknown): SliderMode => {
  return SLIDER_MODES.includes(value as SliderMode)
    ? (value as SliderMode)
    : 'browser'
}

export const updateSliderMode = (mode: SliderMode): Promise<ApiResponse> => {
  return put<ApiResponse>(SLIDER_MODE_URL, { value: mode })
}
