<template>
  <div class="gs-container">
    <!-- 금/은 가격 비교 -->
    <div class="gs-body">
      <h1 class="gs-title">금/은 가격 비교</h1>
      
      <!-- 자산 선택 및 날짜 선택 -->
      <div class="gs-controls">
        <select class="gs-select" v-model="assetType" @change="fetchPriceData">
          <option value="gold">금</option>
          <option value="silver">은</option>
        </select>

        <label for="startDate" class="gs-label">시작 날짜</label>
        <input type="date" id="startDate" class="gs-input" v-model="startDate" />

        <label for="endDate" class="gs-label">종료 날짜</label>
        <input type="date" id="endDate" class="gs-input" v-model="endDate" />

        <button @click="fetchPriceData" class="gs-button">조회</button>
      </div>

      <!-- 오류 메시지 -->
      <div v-if="errorMessage" class="gs-error-message">{{ errorMessage }}</div>

      <!-- 차트 컨테이너 -->
      <div class="gs-chart-container">
        <canvas ref="myChart" class="gs-chart"></canvas>
      </div>
    </div>

    <footer class="gs-footer">
      <p>© 2025 Bankbook</p>
    </footer>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import Chart from 'chart.js/auto';
import 'chartjs-adapter-date-fns';  // 날짜 어댑터 추가

export default {
  data() {
    return {
      assetType: 'gold',  // 기본 자산은 'gold'
      startDate: '',
      endDate: '',
      priceData: [],
      chartInstance: null,
      errorMessage: '',
    };
  },
  mounted() {
    // 페이지 로드시 금의 전체 데이터(2023-01-01 ~ 2024-12-31) 로드
    this.startDate = '2023-01-01';
    this.endDate = '2024-12-31';
    this.fetchPriceData();
  },
  methods: {
    async fetchPriceData() {
      try {
        // 기본 날짜 범위 설정
        if (!this.startDate || !this.endDate) {
          this.startDate = '2023-01-01';
          this.endDate = '2024-12-31';
        }

        // 날짜 비교 (시작일이 종료일 이후면 오류 메시지 출력)
        if (new Date(this.startDate) > new Date(this.endDate)) {
          this.errorMessage = '시작일이 종료일보다 클 수 없습니다.';
          return;
        }

        const response = await fetch(`http://127.0.0.1:8000/gold_silver/get_price_data/?asset_type=${this.assetType}&start_date=${this.startDate}&end_date=${this.endDate}`);
        const data = await response.json();

        if (data.status === 'success') {
          this.priceData = data.data;

          // 금 가격이 문자열로 되어 있다면 숫자로 변환 (콤마 제거 후 parseFloat)
          if (this.assetType === 'gold') {
            this.priceData = this.priceData.map(item => ({
              Date: item.Date,
              'Close/Last': parseFloat(item['Close/Last'].replace(/,/g, ''))  // ','를 제거한 후 숫자로 변환
            }));
          }

          // 차트 렌더링
          this.renderChart();
          this.errorMessage = ''; // 오류 메시지 초기화
        } else {
          this.errorMessage = '데이터 조회에 실패했습니다';
        }
      } catch (error) {
        console.error('API 호출 오류:', error);
        this.errorMessage = '서버와의 연결에 실패했습니다';
      }
    },

    renderChart() {
      const ctx = this.$refs.myChart.getContext('2d');
      
      // 데이터가 정상적으로 로드되었는지 확인
      console.log('Dates:', this.priceData.map(item => item.Date));
      console.log('Prices:', this.priceData.map(item => item['Close/Last']));

      // 기존 차트가 있으면 제거
      if (this.chartInstance) {
        this.chartInstance.destroy();
      }

      // 날짜 데이터를 Date 객체로 변환
      const dates = this.priceData.map(item => new Date(item.Date));  // Date 객체로 변환
      const prices = this.priceData.map(item => item['Close/Last']);

      // 새로운 차트 생성
      this.chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels: dates,
          datasets: [{
            label: `${this.assetType === 'gold' ? '금' : '은'} 가격`,
            data: prices,
            borderColor: 'gold',
            fill: false,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,  // 비율 유지 하지 않음 (차트 크기 변경 시 비율을 맞추지 않도록)
          scales: {
            x: {
              type: 'time',
              time: {
                unit: 'day',
                tooltipFormat: 'll',
              },
              title: {
                display: true,
                text: '날짜',
              },
            },
            y: {
              title: {
                display: true,
                text: '가격',
              },
              ticks: {
                min: Math.min(...prices) - 50,  // 최소값 설정
                max: Math.max(...prices) + 50,  // 최대값 설정
              },
            },
          },
        },
      });
    },
  },
};
</script>

<style scoped>
.error {
  color: red;
}

.chart-container {
  width: 100%;
  height: 400px;
  margin: 0 auto;
}
</style>
