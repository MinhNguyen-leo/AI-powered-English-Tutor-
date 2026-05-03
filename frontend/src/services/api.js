import axios from "axios";
import API_BASE from "../config";

const api = axios.create({ baseURL: API_BASE, timeout: 30000 });

export const sendChatMessage = (userId, message) =>
  api.post("/chat", { user_id: userId, message });

export const sendWritingText = (userId, text, taskType = "Task 2") =>
  api.post("/writing", { user_id: userId, text, task_type: taskType });

export const getMemoryStats = (userId) =>
  api.get(`/memory/${userId}/stats`);

export const getMemoryErrors = (userId, limit = 20) =>
  api.get(`/memory/${userId}/errors`, { params: { limit } });
