"""
Основное Streamlit приложение
UI для анализа фармацевтических текстов
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import json

from config import settings
from database import postgres_manager, clickhouse_manager
from redis_queue import queue_manager

# Настройка страницы
st.set_page_config(
    page_title=settings.page_title,
    page_icon=settings.page_icon,
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
            # Отправляем задачу в очередь
            result = queue_manager.enqueue_text_analysis(
                text=text.strip(),
                source_url=source_url if source_url else None,
                source_date=source_date.isoformat() if source_date else None,
                force_recheck=force_recheck
            )
            
            if result['status'] == 'enqueued':
                st.success(f"✅ Задача отправлена! ID: {result['job_id']}")
                
                # Сохраняем ID задачи в session state
                st.session_state['current_job_id'] = result['job_id']
                st.session_state['job_submitted'] = True
                
            else:
                st.error(f"❌ Ошибка: {result.get('reason', 'Неизвестная ошибка')}")
    
    # Отображение статуса текущей задачи
    if 'current_job_id' in st.session_state and st.session_state.get('job_submitted'):
        st.subheader("📊 Статус задачи")
        
        # Автообновление статуса
        if st.button("🔄 Обновить статус"):
            st.rerun()
        
        # Получаем статус задачи
        job_status = queue_manager.get_job_status(st.session_state['current_job_id'])
        
        # Получаем промежуточные результаты
        progress_data = queue_manager.get_job_progress(st.session_state['current_job_id'])
        
        # Отображаем статус
        status = job_status.get('status', 'unknown')
        
        if status == 'finished':
            st.success("✅ Анализ завершен!")
            show_job_results(job_status.get('result', {}))
            st.session_state['job_submitted'] = False
            
        elif status == 'failed':
            st.error("❌ Анализ завершился с ошибкой")
            st.error(f"Ошибка: {job_status.get('error', 'Неизвестная ошибка')}")
            st.session_state['job_submitted'] = False
            
        elif status == 'started':
            st.info("🔄 Анализ выполняется...")
            # Показываем промежуточные результаты
            show_job_progress(progress_data)
            
        elif status == 'queued':
            st.warning("⏳ Задача в очереди...")
            # Показываем промежуточные результаты если они есть
            if progress_data.get('status') != 'not_found':
                show_job_progress(progress_data)
            
        else:
            st.info(f"📋 Статус: {status}")
            # Показываем промежуточные результаты если они есть
            if progress_data.get('status') != 'not_found':
                show_job_progress(progress_data)


def show_job_progress(progress_data):
    """Отображение промежуточных результатов анализа"""
    if not progress_data or progress_data.get('status') == 'not_found':
        st.info("📊 Промежуточные результаты недоступны")
        return
    
    st.subheader("🔄 Промежуточные результаты анализа")
    
    # Основная информация о прогрессе
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Прогресс", progress_data.get('progress', 'N/A'))
    
    with col2:
        st.metric("Текущий критерий", progress_data.get('current_criterion', 'N/A'))
    
    with col3:
        st.metric("Статус", progress_data.get('status', 'N/A'))
    
    # Текущий критерий
    if 'criterion_text' in progress_data:
        st.subheader("📝 Текущий критерий")
        st.info(f"**{progress_data.get('current_criterion', 'N/A')}**: {progress_data['criterion_text']}")
    
    # Результат текущего анализа
    if 'current_result' in progress_data:
        result = progress_data['current_result']
        st.subheader("🤖 Результат анализа Ollama")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            match_status = "✅ Совпадение" if result.get('is_match') else "❌ Не совпадает"
            st.metric("Результат", match_status)
        
        with col2:
            st.metric("Уверенность", f"{result.get('confidence', 0):.2f}")
        
        with col3:
            st.metric("Время (мс)", result.get('latency_ms', 0))
        
        # Краткое описание
        if 'summary' in result and result['summary']:
            st.subheader("📄 Краткое описание")
            st.info(result['summary'])
        
        # Информация о модели
        if 'model_name' in result:
            st.caption(f"Модель: {result['model_name']}")


def show_job_results(result):
    """Отображение результатов анализа"""
    if not result:
        st.warning("Нет результатов для отображения")
        return
    
    st.subheader("📋 Результаты анализа")
    
    # Основная статистика
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Статус", result.get('status', 'N/A'))
    
    with col2:
        st.metric("Всего событий", result.get('total_events', 0))
    
    with col3:
        st.metric("Совпадения", result.get('matches', 0))
    
    with col4:
        st.metric("Средняя уверенность", f"{result.get('avg_confidence', 0):.2f}")
    
    # Детали событий
    if 'events' in result and result['events']:
        st.subheader("📝 Детали событий")
        
        events_df = pd.DataFrame(result['events'])
        
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
    
    try:
        # Статистика по критериям
        criteria_stats = clickhouse_manager.get_criteria_stats(days)
        
        if criteria_stats:
            stats_df = pd.DataFrame(criteria_stats)
            
            # Основные метрики
            st.subheader("📊 Основные показатели")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_events = stats_df['total_events'].sum()
                st.metric("Всего событий", total_events)
            
            with col2:
                total_matches = stats_df['matches'].sum()
                match_rate = (total_matches / total_events * 100) if total_events > 0 else 0
                st.metric("Всего совпадений", f"{total_matches} ({match_rate:.1f}%)")
            
            with col3:
                avg_confidence = stats_df['avg_confidence'].mean()
                st.metric("Средняя уверенность", f"{avg_confidence:.2f}")
            
            with col4:
                avg_latency = stats_df['avg_latency_ms'].mean()
                st.metric("Среднее время (мс)", f"{avg_latency:.0f}")
            
            # Детальная статистика по критериям
            st.subheader("📋 Статистика по критериям")
            
            # Создаем таблицу с детальной статистикой
            display_df = stats_df.copy()
            display_df['match_rate'] = (display_df['matches'] / display_df['total_events'] * 100).round(1)
            display_df = display_df.rename(columns={
                'criterion_id': 'Критерий',
                'total_events': 'Всего событий',
                'matches': 'Совпадения',
                'match_rate': 'Процент совпадений (%)',
                'avg_confidence': 'Средняя уверенность',
                'avg_latency_ms': 'Среднее время (мс)'
            })
            
            st.dataframe(
                display_df[['Критерий', 'Всего событий', 'Совпадения', 'Процент совпадений (%)', 
                           'Средняя уверенность', 'Среднее время (мс)']],
                use_container_width=True
            )
            
            # Графики
            st.subheader("📊 Графики")
            col1, col2 = st.columns(2)
            
            with col1:
                # График событий по критериям
                fig1 = px.bar(
                    stats_df,
                    x='criterion_id',
                    y='total_events',
                    title="События по критериям",
                    labels={'criterion_id': 'Критерий', 'total_events': 'Количество событий'},
                    color='total_events',
                    color_continuous_scale='Blues'
                )
                fig1.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                # График совпадений по критериям
                fig2 = px.bar(
                    stats_df,
                    x='criterion_id',
                    y='matches',
                    title="Совпадения по критериям",
                    labels={'criterion_id': 'Критерий', 'matches': 'Количество совпадений'},
                    color='matches',
                    color_continuous_scale='Greens'
                )
                fig2.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig2, use_container_width=True)
            
            # График процента совпадений
            fig3 = px.bar(
                stats_df,
                x='criterion_id',
                y=stats_df['matches'] / stats_df['total_events'] * 100,
                title="Процент совпадений по критериям",
                labels={'criterion_id': 'Критерий', 'y': 'Процент совпадений (%)'},
                color=stats_df['matches'] / stats_df['total_events'] * 100,
                color_continuous_scale='Viridis'
            )
            fig3.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig3, use_container_width=True)
            
            # Ежедневная статистика
            daily_stats = clickhouse_manager.get_daily_stats(days)
            
            if daily_stats:
                daily_df = pd.DataFrame(daily_stats)
                daily_df['date'] = pd.to_datetime(daily_df['date'])
                
                st.subheader("📅 Ежедневная статистика")
                
                # Метрики по дням
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    avg_daily_events = daily_df['total_events'].mean()
                    st.metric("Среднее событий в день", f"{avg_daily_events:.1f}")
                
                with col2:
                    avg_daily_matches = daily_df['matches'].mean()
                    st.metric("Среднее совпадений в день", f"{avg_daily_matches:.1f}")
                
                with col3:
                    avg_daily_confidence = daily_df['avg_confidence'].mean()
                    st.metric("Средняя уверенность", f"{avg_daily_confidence:.2f}")
                
                # График ежедневной статистики
                fig4 = px.line(
                    daily_df,
                    x='date',
                    y=['total_events', 'matches'],
                    title="События и совпадения по дням",
                    labels={'date': 'Дата', 'value': 'Количество', 'variable': 'Тип'},
                    markers=True
                )
                fig4.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig4, use_container_width=True)
                
                # График уверенности по дням
                fig5 = px.line(
                    daily_df,
                    x='date',
                    y='avg_confidence',
                    title="Средняя уверенность по дням",
                    labels={'date': 'Дата', 'avg_confidence': 'Уверенность'},
                    markers=True
                )
                fig5.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig5, use_container_width=True)
        
        else:
            st.info("📊 Нет данных для отображения")
    
    except Exception as e:
        st.error(f"❌ Ошибка загрузки статистики: {e}")
        st.exception(e)


def show_history_page():
    """Страница истории"""
    st.header("🔍 История")
    
    # Фильтры
    col1, col2 = st.columns(2)
    
    with col1:
        limit = st.selectbox("Количество записей:", [10, 25, 50, 100], index=3)
    
    with col2:
        if st.button("🔄 Обновить"):
            st.rerun()
    
    try:
        # Получаем последние события
        events = clickhouse_manager.get_recent_events(limit)
        
        if events:
            events_df = pd.DataFrame(events)
            
            # Конвертируем даты
            if 'ingest_ts' in events_df.columns:
                events_df['ingest_ts'] = pd.to_datetime(events_df['ingest_ts'])
            
            # Отображаем таблицу
            st.subheader("📋 Последние события")
            
            # Фильтры для таблицы
            show_matches_only = st.checkbox("Только совпадения")
            
            if show_matches_only:
                events_df = events_df[events_df['is_match'] == 1]
            
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
    
    except Exception as e:
        st.error(f"❌ Ошибка загрузки истории: {e}")


def show_settings_page():
    """Страница настроек"""
    st.header("⚙️ Настройки")
    
    # Статус сервисов
    st.subheader("🔧 Статус сервисов")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Проверка Redis
        try:
            queue_info = queue_manager.get_queue_info()
            if 'status' not in queue_info:
                st.success("✅ Redis - подключен")
                st.info(f"Очередь: {queue_info.get('queue_length', 0)} задач")
            else:
                st.error("❌ Redis - недоступен")
        except:
            st.error("❌ Redis - недоступен")
    
    with col2:
        # Проверка баз данных
        try:
            # Проверяем PostgreSQL
            criteria = postgres_manager.get_active_criteria()
            st.success("✅ PostgreSQL - подключен")
            st.info(f"Критериев: {len(criteria)}")
        except:
            st.error("❌ PostgreSQL - недоступен")
    
    # Управление очередью
    st.subheader("📋 Управление очередью")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Очистить очередь"):
            result = queue_manager.clear_queue()
            if result['status'] == 'cleared':
                st.success(f"✅ Очередь очищена ({result['cleared_jobs']} задач)")
            else:
                st.error(f"❌ Ошибка: {result.get('reason', 'Неизвестная ошибка')}")
    
    with col2:
        if st.button("📊 Информация о очереди"):
            queue_info = queue_manager.get_queue_info()
            if 'status' not in queue_info:
                st.info(f"Очередь: {queue_info.get('queue_name', 'N/A')}")
                st.info(f"Задач в очереди: {queue_info.get('queue_length', 0)}")
                st.info(f"Рабочих процессов: {queue_info.get('workers', 0)}")
            else:
                st.error(f"❌ Ошибка: {queue_info.get('reason', 'Неизвестная ошибка')}")


if __name__ == "__main__":
    main()
