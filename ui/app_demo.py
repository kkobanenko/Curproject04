"""
Демо-версия Streamlit приложения для тестирования
Без внешних зависимостей от Redis, PostgreSQL, ClickHouse
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import json
import random

# Настройка страницы
st.set_page_config(
    page_title="Анализ фармацевтических текстов",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS стили
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    .status-pending {
        color: #ffc107;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


def generate_mock_data():
    """Генерация тестовых данных"""
    criteria = ['molecules_pretrial_v1', 'drug_safety_v1', 'clinical_trials_v1']
    
    # Генерация событий
    events = []
    for i in range(50):
        events.append({
            'event_id': f'event_{i}',
            'source_hash': f'hash_{i}',
            'source_url': f'https://example.com/article_{i}',
            'source_date': datetime.now() - timedelta(days=random.randint(0, 30)),
            'ingest_ts': datetime.now() - timedelta(hours=random.randint(0, 720)),
            'criterion_id': random.choice(criteria),
            'criterion_text': 'Тестовый критерий',
            'is_match': random.choice([True, False]),
            'confidence': round(random.uniform(0.1, 0.95), 2),
            'summary': f'Резюме анализа для события {i}',
            'model_name': 'llama3:8b',
            'latency_ms': random.randint(800, 3000),
            'created_at': datetime.now()
        })
    
    return events


def main():
    """Основная функция приложения"""
    
    # Заголовок
    st.markdown('<h1 class="main-header">💊 Анализ фармацевтических текстов</h1>', 
                unsafe_allow_html=True)
    
    # Боковая панель
    with st.sidebar:
        st.header("📊 Навигация")
        page = st.selectbox(
            "Выберите раздел:",
            ["📝 Анализ текста", "📈 Статистика", "🔍 История", "⚙️ Настройки"]
        )
    
    # Отображение страниц
    if page == "📝 Анализ текста":
        show_text_analysis_page()
    elif page == "📈 Статистика":
        show_statistics_page()
    elif page == "🔍 История":
        show_history_page()
    elif page == "⚙️ Настройки":
        show_settings_page()


def show_text_analysis_page():
    """Страница анализа текста"""
    st.header("📝 Анализ текста")
    
    # Форма ввода
    with st.form("text_analysis_form"):
        st.subheader("Введите текст для анализа")
        
        text = st.text_area(
            "Текст:",
            height=200,
            placeholder="Введите текст для анализа по критериям..."
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            source_url = st.text_input(
                "URL источника (опционально):",
                placeholder="https://example.com/article"
            )
        
        with col2:
            source_date = st.date_input(
                "Дата источника (опционально):",
                value=None
            )
        
        force_recheck = st.checkbox("Принудительная перепроверка")
        
        submitted = st.form_submit_button("🚀 Отправить на анализ")
    
    # Обработка отправки формы
    if submitted and text.strip():
        with st.spinner("Отправляем задачу в очередь..."):
            time.sleep(2)  # Имитация задержки
            
            # Имитируем успешную отправку
            job_id = f"job_{int(time.time())}"
            st.success(f"✅ Задача отправлена! ID: {job_id}")
            
            # Сохраняем ID задачи в session state
            st.session_state['current_job_id'] = job_id
            st.session_state['job_submitted'] = True
    
    # Отображение статуса текущей задачи
    if 'current_job_id' in st.session_state and st.session_state.get('job_submitted'):
        st.subheader("📊 Статус задачи")
        
        # Имитируем статус задачи
        status = random.choice(['queued', 'started', 'finished'])
        
        if status == 'finished':
            st.success("✅ Анализ завершен!")
            show_mock_job_results()
            st.session_state['job_submitted'] = False
            
        elif status == 'started':
            st.info("🔄 Анализ выполняется...")
            
        elif status == 'queued':
            st.warning("⏳ Задача в очереди...")


def show_mock_job_results():
    """Отображение результатов анализа (мок)"""
    st.subheader("📋 Результаты анализа")
    
    # Генерируем мок данные
    events = generate_mock_data()[:5]  # Только 5 событий для демо
    
    # Основная статистика
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Статус", "success")
    
    with col2:
        st.metric("Всего событий", len(events))
    
    with col3:
        matches = sum(1 for e in events if e['is_match'])
        st.metric("Совпадения", matches)
    
    with col4:
        avg_confidence = sum(e['confidence'] for e in events) / len(events)
        st.metric("Средняя уверенность", f"{avg_confidence:.2f}")
    
    # Детали событий
    st.subheader("📝 Детали событий")
    
    events_df = pd.DataFrame(events)
    
    # Отображаем таблицу событий
    st.dataframe(
        events_df[['criterion_id', 'is_match', 'confidence', 'summary', 'latency_ms']],
        use_container_width=True
    )
    
    # График уверенности
    if len(events_df) > 1:
        fig = px.bar(
            events_df,
            x='criterion_id',
            y='confidence',
            color='is_match',
            title="Уверенность по критериям",
            labels={'criterion_id': 'Критерий', 'confidence': 'Уверенность'}
        )
        st.plotly_chart(fig, use_container_width=True)


def show_statistics_page():
    """Страница статистики"""
    st.header("📈 Статистика")
    
    # Период статистики
    col1, col2 = st.columns(2)
    
    with col1:
        days = st.selectbox("Период:", [7, 30, 90], index=1)
    
    with col2:
        if st.button("🔄 Обновить статистику"):
            st.rerun()
    
    # Основные метрики
    st.subheader("📊 Основные показатели")
    
    # Генерируем мок статистику
    events = generate_mock_data()
    stats_df = pd.DataFrame(events)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_events = len(stats_df)
        st.metric("Всего событий", total_events)
    
    with col2:
        total_matches = stats_df['is_match'].sum()
        st.metric("Всего совпадений", total_matches)
    
    with col3:
        avg_confidence = stats_df['confidence'].mean()
        st.metric("Средняя уверенность", f"{avg_confidence:.2f}")
    
    with col4:
        avg_latency = stats_df['latency_ms'].mean()
        st.metric("Среднее время (мс)", f"{avg_latency:.0f}")
    
    # Графики
    col1, col2 = st.columns(2)
    
    with col1:
        # График событий по критериям
        criteria_stats = stats_df.groupby('criterion_id').size().reset_index(name='total_events')
        fig1 = px.bar(
            criteria_stats,
            x='criterion_id',
            y='total_events',
            title="События по критериям",
            labels={'criterion_id': 'Критерий', 'total_events': 'Количество событий'}
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # График совпадений по критериям
        matches_stats = stats_df.groupby('criterion_id')['is_match'].sum().reset_index()
        fig2 = px.bar(
            matches_stats,
            x='criterion_id',
            y='is_match',
            title="Совпадения по критериям",
            labels={'criterion_id': 'Критерий', 'is_match': 'Количество совпадений'}
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # Ежедневная статистика
    st.subheader("📅 Ежедневная статистика")
    
    # Генерируем ежедневную статистику
    daily_data = []
    for i in range(7):
        date = datetime.now() - timedelta(days=i)
        daily_data.append({
            'date': date.date(),
            'total_events': random.randint(5, 20),
            'matches': random.randint(1, 8),
            'avg_confidence': round(random.uniform(0.4, 0.8), 2),
            'avg_latency_ms': random.randint(1000, 2000)
        })
    
    daily_df = pd.DataFrame(daily_data)
    daily_df['date'] = pd.to_datetime(daily_df['date'])
    
    fig3 = px.line(
        daily_df,
        x='date',
        y=['total_events', 'matches'],
        title="События и совпадения по дням",
        labels={'date': 'Дата', 'value': 'Количество', 'variable': 'Тип'}
    )
    st.plotly_chart(fig3, use_container_width=True)


def show_history_page():
    """Страница истории"""
    st.header("🔍 История")
    
    # Фильтры
    col1, col2 = st.columns(2)
    
    with col1:
        limit = st.selectbox("Количество записей:", [10, 25, 50, 100], index=2)
    
    with col2:
        if st.button("🔄 Обновить"):
            st.rerun()
    
    # Генерируем мок события
    events = generate_mock_data()[:limit]
    
    if events:
        events_df = pd.DataFrame(events)
        
        # Конвертируем даты
        events_df['ingest_ts'] = pd.to_datetime(events_df['ingest_ts'])
        
        # Отображаем таблицу
        st.subheader("📋 Последние события")
        
        # Фильтры для таблицы
        show_matches_only = st.checkbox("Только совпадения")
        
        if show_matches_only:
            events_df = events_df[events_df['is_match'] == True]
        
        if not events_df.empty:
            # Переименовываем колонки для лучшего отображения
            display_df = events_df.copy()
            display_df = display_df.rename(columns={
                'ingest_ts': 'Дата анализа',
                'criterion_text': 'Критерий',
                'is_match': 'Совпадение',
                'confidence': 'Уверенность',
                'summary': 'Результат'
            })
            
            st.dataframe(
                display_df[['Дата анализа', 'Критерий', 'Совпадение', 'Уверенность', 'Результат']],
                use_container_width=True
            )
        else:
            st.info("📊 Нет событий для отображения")
    
    else:
        st.info("📊 Нет данных для отображения")


def show_settings_page():
    """Страница настроек"""
    st.header("⚙️ Настройки")
    
    # Статус сервисов
    st.subheader("🔧 Статус сервисов")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Имитируем статус Redis
        st.success("✅ Redis - подключен")
        st.info("Очередь: 0 задач")
    
    with col2:
        # Имитируем статус PostgreSQL
        st.success("✅ PostgreSQL - подключен")
        st.info("Критериев: 3")
    
    # Управление очередью
    st.subheader("📋 Управление очередью")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Очистить очередь"):
            st.success("✅ Очередь очищена (0 задач)")
    
    with col2:
        if st.button("📊 Информация о очереди"):
            st.info("Очередь: text_analysis")
            st.info("Задач в очереди: 0")
            st.info("Рабочих процессов: 0")


if __name__ == "__main__":
    main()
