import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({ baseURL: BASE })

export const getDashboard = () => api.get('/api/dashboard').then(r => r.data)
export const getVideos = (stage) => api.get('/api/videos', { params: stage ? { stage } : {} }).then(r => r.data)
export const getVideo = (id) => api.get(`/api/videos/${id}`).then(r => r.data)
export const getPipeline = () => api.get('/api/pipeline').then(r => r.data)
export const proposeIdeas = (count = 3) => api.post(`/api/ideas/propose?count=${count}`).then(r => r.data)
export const approveIdea = (id, decision, feedback) => api.post(`/api/videos/${id}/approve-idea`, { decision, feedback }).then(r => r.data)
export const approveScript = (id, decision, feedback) => api.post(`/api/videos/${id}/approve-script`, { decision, feedback }).then(r => r.data)
export const approveFinal = (id, decision, feedback) => api.post(`/api/videos/${id}/approve-final`, { decision, feedback }).then(r => r.data)
export const approveUpload = (id, decision, feedback) => api.post(`/api/videos/${id}/approve-upload`, { decision, feedback }).then(r => r.data)
export const getVideoSources = (id) => api.get(`/api/videos/${id}/sources`).then(r => r.data)
export const getVideoQA = (id) => api.get(`/api/videos/${id}/qa`).then(r => r.data)
export const getPlatforms = () => api.get('/api/platforms/status').then(r => r.data)
export const autoApprove = (id) => api.post(`/api/videos/${id}/auto-approve`).then(r => r.data)
export const bulkApprove = (stage) => api.post(`/api/bulk-approve?stage=${stage}`).then(r => r.data)
export const generateMetadata = (id) => api.post(`/api/videos/${id}/generate-metadata`).then(r => r.data)
export const updateMetadata = (id, payload) => api.put(`/api/videos/${id}/metadata`, payload).then(r => r.data)
export const setSchedule = (id, scheduled_publish_at) => api.put(`/api/videos/${id}/schedule`, { scheduled_publish_at }).then(r => r.data)
export const getPreviewUrl = (id) => api.get(`/api/videos/${id}/preview-url`).then(r => r.data)
export const triggerUpload = (id) => api.post(`/api/videos/${id}/upload`).then(r => r.data)
export const getYoutubeStatus = () => api.get('/api/platforms/youtube/status').then(r => r.data)
export const getInstagramStatus = () => api.get('/api/platforms/instagram/status').then(r => r.data)
export const getPlatformsStatus = () => api.get('/api/platforms/status').then(r => r.data)
