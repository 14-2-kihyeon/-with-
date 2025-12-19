// src/api/gold_silver.js
import api from './axios';  // axios 인스턴스를 import

// 금 시세 데이터 가져오기
export const getGoldPrices = async () => {
  try {
    const response = await api.get('/gold_silver/gold_prices/');  // 서버에서 gold_prices 데이터를 가져옴
    return response.data;  // 데이터 반환
  } catch (error) {
    console.error("Error fetching gold prices:", error);
    throw error;
  }
};

// 은 시세 데이터 가져오기
export const getSilverPrices = async () => {
  try {
    const response = await api.get('/gold_silver/silver_prices/');  // 서버에서 silver_prices 데이터를 가져옴
    return response.data;  // 데이터 반환
  } catch (error) {
    console.error("Error fetching silver prices:", error);
    throw error;
  }
};
