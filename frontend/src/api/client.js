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
