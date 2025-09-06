"""
Основное Streamlit приложение
UI для анализа фармацевтических текстов
"""

import logging
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import streamlit as st
from config import settings
from database import clickhouse_manager, postgres_manager
from redis_queue import queue_manager

# Настройка логирования
logger = logging.getLogger(__name__)

# Настройка страницы
st.set_page_config(
    page_title=settings.page_title,
    page_icon=settings.page_icon,
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS стили
st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)


def main():
    """Основная функция приложения"""

    # Заголовок
    st.markdown(
        '<h1 class="main-header">💊 Анализ фармацевтических текстов</h1>', unsafe_allow_html=True
    )

    # Боковая панель
    with st.sidebar:
        st.header("📊 Навигация")
        page = st.selectbox(
            "Выберите раздел:",
            ["📝 Анализ текста", "🔍 Поиск новостей", "📈 Статистика", "🔍 История", "⚙️ Настройки"],
        )

    # Отображение страниц
    if page == "📝 Анализ текста":
        show_text_analysis_page()
    elif page == "🔍 Поиск новостей":
        show_news_search_page()
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
            "Текст:", height=200, placeholder="Введите текст для анализа по критериям..."
        )

        col1, col2 = st.columns(2)

        with col1:
            source_url = st.text_input(
                "URL источника (опционально):", placeholder="https://example.com/article"
            )

        with col2:
            source_date = st.date_input("Дата источника (опционально):", value=None)

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
                force_recheck=force_recheck,
            )

            if result["status"] == "enqueued":
                st.success(f"✅ Задача отправлена! ID: {result['job_id']}")

                # Сохраняем ID задачи в session state
                st.session_state["current_job_id"] = result["job_id"]
                st.session_state["job_submitted"] = True

            else:
                st.error(f"❌ Ошибка: {result.get('reason', 'Неизвестная ошибка')}")

    # Отображение статуса текущей задачи
    if "current_job_id" in st.session_state and st.session_state.get("job_submitted"):
        st.subheader("📊 Статус задачи")

        # Автообновление статуса
        if st.button("🔄 Обновить статус"):
            st.rerun()

        # Получаем статус задачи
        job_status = queue_manager.get_job_status(st.session_state["current_job_id"])

        # Получаем промежуточные результаты
        progress_data = queue_manager.get_job_progress(st.session_state["current_job_id"])

        # Отображаем статус
        status = job_status.get("status", "unknown")

        if status == "finished":
            st.success("✅ Анализ завершен!")
            show_job_results(job_status.get("result", {}))
            st.session_state["job_submitted"] = False

        elif status == "failed":
            st.error("❌ Анализ завершился с ошибкой")
            st.error(f"Ошибка: {job_status.get('error', 'Неизвестная ошибка')}")
            st.session_state["job_submitted"] = False

        elif status == "started":
            st.info("🔄 Анализ выполняется...")
            # Показываем промежуточные результаты
            show_job_progress(progress_data)

        elif status == "queued":
            st.warning("⏳ Задача в очереди...")
            # Показываем промежуточные результаты если они есть
            if progress_data.get("status") != "not_found":
                show_job_progress(progress_data)

        else:
            st.info(f"📋 Статус: {status}")
            # Показываем промежуточные результаты если они есть
            if progress_data.get("status") != "not_found":
                show_job_progress(progress_data)


def show_job_progress(progress_data):
    """Отображение промежуточных результатов анализа"""
    if not progress_data or progress_data.get("status") == "not_found":
        st.info("📊 Промежуточные результаты недоступны")
        return

    st.subheader("🔄 Промежуточные результаты анализа")

    # Основная информация о прогрессе
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Прогресс", progress_data.get("progress", "N/A"))

    with col2:
        st.metric("Текущий критерий", progress_data.get("current_criterion", "N/A"))

    with col3:
        st.metric("Статус", progress_data.get("status", "N/A"))

    # Текущий критерий
    if "criterion_text" in progress_data:
        st.subheader("📝 Текущий критерий")
        st.info(
            f"**{progress_data.get('current_criterion', 'N/A')}**: "
            f"{progress_data['criterion_text']}"
        )

    # Результат текущего анализа
    if "current_result" in progress_data:
        result = progress_data["current_result"]
        st.subheader("🤖 Результат анализа Ollama")

        col1, col2, col3 = st.columns(3)

        with col1:
            match_status = "✅ Совпадение" if result.get("is_match") else "❌ Не совпадает"
            st.metric("Результат", match_status)

        with col2:
            st.metric("Уверенность", f"{result.get('confidence', 0):.2f}")

        with col3:
            st.metric("Время (мс)", result.get("latency_ms", 0))

        # Краткое описание
        if "summary" in result and result["summary"]:
            st.subheader("📄 Краткое описание")
            st.info(result["summary"])

        # Информация о модели
        if "model_name" in result:
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
        st.metric("Статус", result.get("status", "N/A"))

    with col2:
        st.metric("Всего событий", result.get("total_events", 0))

    with col3:
        st.metric("Совпадения", result.get("matches", 0))

    with col4:
        st.metric("Средняя уверенность", f"{result.get('avg_confidence', 0):.2f}")

    # Детали событий
    if "events" in result and result["events"]:
        st.subheader("📝 Детали событий")

        events_df = pd.DataFrame(result["events"])

        # Отображаем таблицу событий
        st.dataframe(
            events_df[["criterion_id", "is_match", "confidence", "summary", "latency_ms"]],
            use_container_width=True,
        )

        # График уверенности
        if len(events_df) > 1:
            fig = px.bar(
                events_df,
                x="criterion_id",
                y="confidence",
                color="is_match",
                title="Уверенность по критериям",
                labels={"criterion_id": "Критерий", "confidence": "Уверенность"},
            )
            st.plotly_chart(fig, use_container_width=True)


def show_news_search_page():
    """Страница поиска медицинских новостей"""
    st.header("🔍 Поиск новостей")

    # Импортируем NewsService
    from news_service import NewsService

    news_service = NewsService()

    # Форма поиска новостей
    with st.form("news_search_form"):
        st.subheader("Поиск медицинских новостей")

        # Поле для ввода поискового запроса
        search_query = st.text_input(
            "Поисковый запрос:",
            placeholder="Например: рак легких, диабет, COVID-19...",
            help="Введите медицинскую тему для поиска новостей",
        )

        # Выбор источников новостей
        st.subheader("Источники новостей")

        col1, col2, col3 = st.columns(3)

        with col1:
            pubmed_enabled = st.checkbox(
                "PubMed", value=True, help="Поиск в медицинской литературе PubMed"
            )

        with col2:
            biomcp_enabled = st.checkbox(
                "BioMCP", value=True, help="Поиск через BioMCP (статьи и клинические исследования)"
            )

        with col3:
            web_search_enabled = st.checkbox("Web Search", value=True, help="Поиск в интернете")

        # Настройки поиска
        col1, col2 = st.columns(2)

        with col1:
            limit_per_source = st.number_input(
                "Результатов на источник:",
                min_value=1,
                max_value=20,
                value=5,
                help="Максимальное количество результатов от каждого источника",
            )

        with col2:
            if st.form_submit_button("🔍 Найти новости", use_container_width=True):
                if search_query.strip():
                    # Собираем выбранные источники
                    selected_sources = []
                    if pubmed_enabled:
                        selected_sources.append("pubmed")
                    if biomcp_enabled:
                        selected_sources.append("biomcp")
                    if web_search_enabled:
                        selected_sources.append("web_search")

                    if selected_sources:
                        # Выполняем поиск
                        with st.spinner("Поиск новостей..."):
                            try:
                                news_results = news_service.search_medical_news(
                                    query=search_query.strip(),
                                    sources=selected_sources,
                                    limit=limit_per_source,
                                )

                                if news_results:
                                    st.success(f"✅ Найдено {len(news_results)} новостей")

                                    # Сохраняем результаты в session state для отображения
                                    st.session_state["news_search_results"] = news_results
                                    st.session_state["news_search_query"] = search_query.strip()

                                    # Показываем результаты
                                    show_news_search_results(news_results)
                                else:
                                    st.warning("📰 Новости по данному запросу не найдены")

                            except Exception as e:
                                st.error(f"❌ Ошибка поиска новостей: {e}")
                                logger.error(f"Ошибка поиска новостей: {e}")
                    else:
                        st.warning("⚠️ Выберите хотя бы один источник для поиска")
                else:
                    st.warning("⚠️ Введите поисковый запрос")

    # Отображение последних результатов поиска
    if "news_search_results" in st.session_state:
        st.subheader("📰 Последние результаты поиска")
        show_news_search_results(st.session_state["news_search_results"])


def show_news_search_results(news_results: List[Dict[str, Any]]):
    """Отображение результатов поиска новостей"""
    if not news_results:
        st.info("📰 Нет результатов для отображения")
        return

    # Группируем новости по источникам
    sources = {}
    for news in news_results:
        source = news.get("source", "unknown")
        if source not in sources:
            sources[source] = []
        sources[source].append(news)

    # Отображаем новости по источникам
    for source, news_list in sources.items():
        st.subheader(f"📰 {source.upper()}")

        for news in news_list:
            with st.expander(f"📄 {news.get('title', 'Без заголовка')}", expanded=False):
                col1, col2 = st.columns([3, 1])

                with col1:
                    # Основная информация о новости
                    st.write(f"**Источник:** {news.get('source', 'N/A')}")
                    st.write(f"**Дата:** {news.get('created_at', 'N/A')}")

                    if news.get("url"):
                        st.write(f"**URL:** {news['url']}")

                    if news.get("content"):
                        st.write("**Содержание:**")
                        st.text(news["content"])

                with col2:
                    # Кнопки действий
                    if news.get("url"):
                        st.link_button("🔗 Перейти", news["url"], help="Открыть новость в браузере")

                    # Кнопка для передачи в анализ текстов (пока не реализована)
                    st.button(
                        "📝 Анализ текста",
                        key=f"analyze_{news['id']}",
                        help="Передать новость в анализ текстов (в разработке)",
                        disabled=True,
                    )


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
                total_events = stats_df["total_events"].sum()
                st.metric("Всего событий", total_events)

            with col2:
                total_matches = stats_df["matches"].sum()
                match_rate = (total_matches / total_events * 100) if total_events > 0 else 0
                st.metric("Всего совпадений", f"{total_matches} ({match_rate:.1f}%)")

            with col3:
                avg_confidence = stats_df["avg_confidence"].mean()
                st.metric("Средняя уверенность", f"{avg_confidence:.2f}")

            with col4:
                avg_latency = stats_df["avg_latency_ms"].mean()
                st.metric("Среднее время (мс)", f"{avg_latency:.0f}")

            # Детальная статистика по критериям
            st.subheader("📋 Статистика по критериям")

            # Создаем таблицу с детальной статистикой
            display_df = stats_df.copy()
            display_df["match_rate"] = (
                display_df["matches"] / display_df["total_events"] * 100
            ).round(1)
            display_df = display_df.rename(
                columns={
                    "criterion_id": "Критерий",
                    "total_events": "Всего событий",
                    "matches": "Совпадения",
                    "match_rate": "Процент совпадений (%)",
                    "avg_confidence": "Средняя уверенность",
                    "avg_latency_ms": "Среднее время (мс)",
                }
            )

            st.dataframe(
                display_df[
                    [
                        "Критерий",
                        "Всего событий",
                        "Совпадения",
                        "Процент совпадений (%)",
                        "Средняя уверенность",
                        "Среднее время (мс)",
                    ]
                ],
                use_container_width=True,
            )

            # Графики
            st.subheader("📊 Графики")
            col1, col2 = st.columns(2)

            with col1:
                # График событий по критериям
                fig1 = px.bar(
                    stats_df,
                    x="criterion_id",
                    y="total_events",
                    title="События по критериям",
                    labels={"criterion_id": "Критерий", "total_events": "Количество событий"},
                    color="total_events",
                    color_continuous_scale="Blues",
                )
                fig1.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig1, use_container_width=True)

            with col2:
                # График совпадений по критериям
                fig2 = px.bar(
                    stats_df,
                    x="criterion_id",
                    y="matches",
                    title="Совпадения по критериям",
                    labels={"criterion_id": "Критерий", "matches": "Количество совпадений"},
                    color="matches",
                    color_continuous_scale="Greens",
                )
                fig2.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig2, use_container_width=True)

            # График процента совпадений
            fig3 = px.bar(
                stats_df,
                x="criterion_id",
                y=stats_df["matches"] / stats_df["total_events"] * 100,
                title="Процент совпадений по критериям",
                labels={"criterion_id": "Критерий", "y": "Процент совпадений (%)"},
                color=stats_df["matches"] / stats_df["total_events"] * 100,
                color_continuous_scale="Viridis",
            )
            fig3.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig3, use_container_width=True)

            # Ежедневная статистика
            daily_stats = clickhouse_manager.get_daily_stats(days)

            if daily_stats:
                daily_df = pd.DataFrame(daily_stats)
                daily_df["date"] = pd.to_datetime(daily_df["date"])

                st.subheader("📅 Ежедневная статистика")

                # Метрики по дням
                col1, col2, col3 = st.columns(3)

                with col1:
                    avg_daily_events = daily_df["total_events"].mean()
                    st.metric("Среднее событий в день", f"{avg_daily_events:.1f}")

                with col2:
                    avg_daily_matches = daily_df["matches"].mean()
                    st.metric("Среднее совпадений в день", f"{avg_daily_matches:.1f}")

                with col3:
                    avg_daily_confidence = daily_df["avg_confidence"].mean()
                    st.metric("Средняя уверенность", f"{avg_daily_confidence:.2f}")

                # График ежедневной статистики
                fig4 = px.line(
                    daily_df,
                    x="date",
                    y=["total_events", "matches"],
                    title="События и совпадения по дням",
                    labels={"date": "Дата", "value": "Количество", "variable": "Тип"},
                    markers=True,
                )
                fig4.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig4, use_container_width=True)

                # График уверенности по дням
                fig5 = px.line(
                    daily_df,
                    x="date",
                    y="avg_confidence",
                    title="Средняя уверенность по дням",
                    labels={"date": "Дата", "avg_confidence": "Уверенность"},
                    markers=True,
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

    # Подзакладки в истории
    history_tab = st.selectbox("Выберите раздел истории:", ["📋 События", "📰 Новости"])

    if history_tab == "📋 События":
        show_events_history()
    elif history_tab == "📰 Новости":
        show_news_history()


def show_events_history():
    """Отображение истории событий"""
    st.subheader("📋 История событий")

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
            if "ingest_ts" in events_df.columns:
                events_df["ingest_ts"] = pd.to_datetime(events_df["ingest_ts"])

            # Отображаем таблицу
            st.subheader("📋 Последние события")

            # Фильтры для таблицы
            show_matches_only = st.checkbox("Только совпадения")

            if show_matches_only:
                events_df = events_df[events_df["is_match"] == 1]

            if not events_df.empty:
                # Переименовываем колонки для лучшего отображения
                display_df = events_df.copy()
                display_df = display_df.rename(
                    columns={
                        "ingest_ts": "Дата анализа",
                        "criterion_text": "Критерий",
                        "is_match": "Совпадение",
                        "confidence": "Уверенность",
                        "summary": "Результат",
                    }
                )

                # Отображаем таблицу с кнопками действий
                st.subheader("📋 Последние события")

                # Заголовки таблицы
                (
                    header_col1,
                    header_col2,
                    header_col3,
                    header_col4,
                    header_col5,
                    header_col6,
                    header_col7,
                ) = st.columns([2, 3, 1, 1, 1, 1, 1])

                with header_col1:
                    st.write("**📅 Дата анализа**")
                with header_col2:
                    st.write("**📝 Критерий**")
                with header_col3:
                    st.write("**✅ Совпадение**")
                with header_col4:
                    st.write("**📊 Уверенность**")
                with header_col5:
                    st.write("**📄 Результат**")
                with header_col6:
                    st.write("**🔗 Перейти**")
                with header_col7:
                    st.write("**👁️ Просмотр**")

                st.divider()

                # Создаем таблицу с кнопками для каждой строки
                for idx, row in display_df.iterrows():
                    with st.container():
                        col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 3, 1, 1, 1, 1, 1])

                        with col1:
                            st.write(f"**{row['Дата анализа']}**")

                        with col2:
                            st.write(f"**{row['Критерий']}**")

                        with col3:
                            match_icon = "✅" if row["Совпадение"] else "❌"
                            st.write(f"{match_icon}")

                        with col4:
                            st.write(f"{row['Уверенность']:.2f}")

                        with col5:
                            st.write(
                                f"{row['Результат'][:50]}..."
                                if len(str(row["Результат"])) > 50
                                else row["Результат"]
                            )

                        with col6:
                            # Кнопка "Перейти" - только если есть URL
                            source_url = events_df.iloc[idx]["source_url"]
                            if source_url and source_url != "\\N":
                                st.link_button(
                                    "🔗 Перейти", source_url, help="Открыть исходный документ"
                                )
                            else:
                                st.write("—")

                        with col7:
                            # Кнопка "Просмотр" - показать текст в модальном окне
                            source_hash = events_df.iloc[idx]["source_hash"]
                            if st.button(
                                "👁️ Просмотр", key=f"view_{idx}", help="Просмотр текста документа"
                            ):
                                st.session_state[f"show_text_{idx}"] = True

                        # Модальное окно для просмотра текста
                        if st.session_state.get(f"show_text_{idx}", False):
                            with st.expander(
                                f"📄 Текст документа (строка {idx + 1})", expanded=True
                            ):
                                try:
                                    # Получаем текст источника по хешу
                                    source_data = postgres_manager.get_source_by_hash(source_hash)
                                    if source_data and source_data.get("text"):
                                        st.text_area(
                                            "Текст документа:",
                                            value=source_data["text"],
                                            height=300,
                                            disabled=True,
                                        )

                                        # Дополнительная информация
                                        col_info1, col_info2 = st.columns(2)
                                        with col_info1:
                                            if source_data.get("url"):
                                                st.write(f"**URL:** {source_data['url']}")
                                        with col_info2:
                                            if source_data.get("date"):
                                                st.write(f"**Дата:** {source_data['date']}")
                                    else:
                                        st.warning("📄 Текст документа недоступен")

                                except Exception as e:
                                    st.error(f"❌ Ошибка загрузки текста: {e}")

                                # Кнопка закрытия
                                if st.button("❌ Закрыть", key=f"close_{idx}"):
                                    st.session_state[f"show_text_{idx}"] = False
                                    st.rerun()

                        st.divider()
            else:
                st.info("📊 Нет событий для отображения")

        else:
            st.info("📊 Нет данных для отображения")

    except Exception as e:
        st.error(f"❌ Ошибка загрузки истории: {e}")


def show_news_history():
    """Отображение истории новостей"""
    st.subheader("📰 История новостей")

    # Фильтры
    col1, col2 = st.columns(2)

    with col1:
        limit = st.selectbox("Количество записей:", [10, 25, 50, 100], index=3, key="news_limit")

    with col2:
        if st.button("🔄 Обновить", key="news_refresh"):
            st.rerun()

    try:
        # Получаем последние новости
        news_list = postgres_manager.get_news(limit)

        if news_list:
            # Отображаем таблицу новостей
            st.subheader("📰 Последние новости")

            # Фильтры для таблицы
            col1, col2 = st.columns(2)

            with col1:
                show_source_filter = st.selectbox(
                    "Фильтр по источнику:",
                    ["Все источники"]
                    + list(set([news.get("source", "unknown") for news in news_list])),
                    key="news_source_filter",
                )

            with col2:
                if st.button("🗑️ Очистить фильтры", key="clear_news_filters"):
                    st.rerun()

            # Применяем фильтр по источнику
            if show_source_filter != "Все источники":
                news_list = [news for news in news_list if news.get("source") == show_source_filter]

            if news_list:
                # Отображаем таблицу с кнопками действий
                st.subheader("📰 Последние новости")

                # Заголовки таблицы
                (
                    header_col1,
                    header_col2,
                    header_col3,
                    header_col4,
                    header_col5,
                    header_col6,
                    header_col7,
                ) = st.columns([2, 3, 1, 1, 1, 1, 1])

                with header_col1:
                    st.write("**📅 Дата создания**")
                with header_col2:
                    st.write("**📝 Заголовок**")
                with header_col3:
                    st.write("**📰 Источник**")
                with header_col4:
                    st.write("**🔍 Запрос**")
                with header_col5:
                    st.write("**📄 Содержание**")
                with header_col6:
                    st.write("**🔗 Перейти**")
                with header_col7:
                    st.write("**👁️ Просмотр**")

                st.divider()

                # Создаем таблицу с кнопками для каждой строки
                for idx, news in enumerate(news_list):
                    with st.container():
                        col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 3, 1, 1, 1, 1, 1])

                        with col1:
                            created_at = news.get("created_at", "N/A")
                            if created_at != "N/A":
                                try:
                                    created_at = pd.to_datetime(created_at).strftime(
                                        "%Y-%m-%d %H:%M"
                                    )
                                except Exception:
                                    pass
                            st.write(f"**{created_at}**")

                        with col2:
                            title = news.get("title", "Без заголовка")
                            st.write(f"**{title[:50]}{'...' if len(title) > 50 else ''}**")

                        with col3:
                            source = news.get("source", "N/A")
                            st.write(f"**{source}**")

                        with col4:
                            search_query = news.get("search_query", "N/A")
                            st.write(
                                f"**{search_query[:20]}{'...' if len(search_query) > 20 else ''}**"
                            )

                        with col5:
                            content = news.get("content", "")
                            if content:
                                st.write(f"{content[:30]}{'...' if len(content) > 30 else ''}")
                            else:
                                st.write("—")

                        with col6:
                            # Кнопка "Перейти" - только если есть URL
                            url = news.get("url")
                            if url:
                                st.link_button("🔗 Перейти", url, help="Открыть новость в браузере")
                            else:
                                st.write("—")

                        with col7:
                            # Кнопка "Просмотр" - показать текст в модальном окне
                            if st.button(
                                "👁️ Просмотр", key=f"view_news_{idx}", help="Просмотр новости"
                            ):
                                st.session_state[f"show_news_{idx}"] = True

                        # Модальное окно для просмотра новости
                        if st.session_state.get(f"show_news_{idx}", False):
                            with st.expander(f"📄 Новость (строка {idx + 1})", expanded=True):
                                try:
                                    # Отображаем полную информацию о новости
                                    st.write(f"**Заголовок:** {news.get('title', 'N/A')}")
                                    st.write(f"**Источник:** {news.get('source', 'N/A')}")
                                    st.write(
                                        f"**Поисковый запрос:** {news.get('search_query', 'N/A')}"
                                    )
                                    st.write(f"**Дата создания:** {news.get('created_at', 'N/A')}")

                                    if news.get("url"):
                                        st.write(f"**URL:** {news['url']}")

                                    if news.get("content"):
                                        st.text_area(
                                            "Содержание новости:",
                                            value=news["content"],
                                            height=300,
                                            disabled=True,
                                        )
                                    else:
                                        st.warning("📄 Содержание новости недоступно")

                                except Exception as e:
                                    st.error(f"❌ Ошибка загрузки новости: {e}")

                                # Кнопка закрытия
                                if st.button("❌ Закрыть", key=f"close_news_{idx}"):
                                    st.session_state[f"show_news_{idx}"] = False
                                    st.rerun()

                        st.divider()
            else:
                st.info("📰 Нет новостей для отображения")

        else:
            st.info("📰 Нет данных для отображения")

    except Exception as e:
        st.error(f"❌ Ошибка загрузки истории новостей: {e}")


def show_settings_page():
    """Страница настроек"""
    st.header("⚙️ Настройки")

    # Подзакладки в настройках
    settings_tab = st.selectbox(
        "Выберите раздел настроек:", ["🔧 Статус сервисов", "📋 Управление критериями"]
    )

    if settings_tab == "🔧 Статус сервисов":
        show_services_status()
    elif settings_tab == "📋 Управление критериями":
        show_criteria_management()


def show_services_status():
    """Отображение статуса сервисов"""
    st.subheader("🔧 Статус сервисов")

    col1, col2 = st.columns(2)

    with col1:
        # Проверка Redis
        try:
            queue_info = queue_manager.get_queue_info()
            if "status" not in queue_info:
                st.success("✅ Redis - подключен")
                st.info(f"Очередь: {queue_info.get('queue_length', 0)} задач")
            else:
                st.error("❌ Redis - недоступен")
        except Exception:
            st.error("❌ Redis - недоступен")

    with col2:
        # Проверка баз данных
        try:
            # Проверяем PostgreSQL
            criteria = postgres_manager.get_active_criteria()
            st.success("✅ PostgreSQL - подключен")
            st.info(f"Критериев: {len(criteria)}")
        except Exception:
            st.error("❌ PostgreSQL - недоступен")

    # Управление очередью
    st.subheader("📋 Управление очередью")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Очистить очередь"):
            result = queue_manager.clear_queue()
            if result["status"] == "cleared":
                st.success(f"✅ Очередь очищена ({result['cleared_jobs']} задач)")
            else:
                st.error(f"❌ Ошибка: {result.get('reason', 'Неизвестная ошибка')}")

    with col2:
        if st.button("📊 Информация о очереди"):
            queue_info = queue_manager.get_queue_info()
            if "status" not in queue_info:
                st.info(f"Очередь: {queue_info.get('queue_name', 'N/A')}")
                st.info(f"Задач в очереди: {queue_info.get('queue_length', 0)}")
                st.info(f"Рабочих процессов: {queue_info.get('workers', 0)}")
            else:
                st.error(f"❌ Ошибка: {queue_info.get('reason', 'Неизвестная ошибка')}")


def show_criteria_management():
    """Отображение управления критериями"""
    st.subheader("📋 Управление критериями")

    # Получаем список всех критериев
    try:
        criteria = postgres_manager.get_criteria()

        if not criteria:
            st.info("📝 Критерии не найдены. Добавьте первый критерий.")
        else:
            # Отображаем таблицу критериев
            st.subheader("📊 Список критериев")

            # Создаем DataFrame для отображения
            criteria_df = pd.DataFrame(criteria)

            # Переименовываем колонки для лучшего отображения
            display_df = criteria_df.copy()
            display_df = display_df.rename(
                columns={
                    "id": "ID",
                    "criterion_text": "Текст критерия",
                    "criteria_version": "Версия",
                    "is_active": "Активен",
                    "threshold": "Порог уверенности",
                    "created_at": "Создан",
                    "updated_at": "Обновлен",
                }
            )

            # Отображаем таблицу
            st.dataframe(
                display_df[["ID", "Текст критерия", "Активен", "Порог уверенности", "Создан"]],
                use_container_width=True,
            )

            # Кнопки управления
            st.subheader("🔧 Действия с критериями")

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("🔄 Обновить список"):
                    st.rerun()

            with col2:
                if st.button("➕ Добавить критерий"):
                    st.session_state["show_add_criterion"] = True

            with col3:
                if st.button("✏️ Редактировать критерий"):
                    st.session_state["show_edit_criterion"] = True

        # Форма добавления критерия
        if st.session_state.get("show_add_criterion", False):
            st.subheader("➕ Добавить новый критерий")

            with st.form("add_criterion_form"):
                criterion_id = st.text_input(
                    "ID критерия:",
                    placeholder="например: molecules_pretrial_v2",
                    help="Уникальный идентификатор критерия",
                )

                criterion_text = st.text_area(
                    "Текст критерия:",
                    height=150,
                    placeholder="Введите текст критерия на русском языке...",
                    help="Описание критерия для анализа текста",
                )

                col1, col2 = st.columns(2)

                with col1:
                    is_active = st.checkbox("Активен", value=True)

                with col2:
                    threshold = st.number_input(
                        "Порог уверенности:",
                        min_value=0.0,
                        max_value=1.0,
                        value=0.5,
                        step=0.1,
                        help="Минимальная уверенность для срабатывания критерия",
                    )

                col1, col2 = st.columns(2)

                with col1:
                    submitted = st.form_submit_button("💾 Сохранить")

                with col2:
                    if st.form_submit_button("❌ Отмена"):
                        st.session_state["show_add_criterion"] = False
                        st.rerun()

                if submitted:
                    if criterion_id and criterion_text:
                        try:
                            pass

                            from models import Criterion

                            # Создаем объект критерия
                            new_criterion = Criterion(
                                id=criterion_id,
                                criterion_text=criterion_text,
                                is_active=is_active,
                                threshold=threshold,
                            )

                            # Сохраняем в базу данных
                            result = postgres_manager.create_criterion(new_criterion)

                            if result:
                                st.success(f"✅ Критерий '{criterion_id}' успешно добавлен!")
                                st.session_state["show_add_criterion"] = False
                                st.rerun()
                            else:
                                st.error("❌ Ошибка при добавлении критерия")

                        except Exception as e:
                            st.error(f"❌ Ошибка: {e}")
                    else:
                        st.error("❌ Заполните все обязательные поля")

        # Форма редактирования критерия
        if st.session_state.get("show_edit_criterion", False):
            st.subheader("✏️ Редактировать критерий")

            # Выбор критерия для редактирования
            if criteria:
                criterion_options = {
                    f"{c['id']} - {c['criterion_text'][:50]}...": c["id"] for c in criteria
                }

                selected_criterion = st.selectbox(
                    "Выберите критерий для редактирования:", options=list(criterion_options.keys())
                )

                if selected_criterion:
                    criterion_id = criterion_options[selected_criterion]
                    criterion_data = postgres_manager.get_criterion_by_id(criterion_id)

                    if criterion_data:
                        with st.form("edit_criterion_form"):
                            st.write(f"**ID:** {criterion_data['id']}")

                            new_criterion_text = st.text_area(
                                "Текст критерия:",
                                value=criterion_data["criterion_text"],
                                height=150,
                            )

                            col1, col2 = st.columns(2)

                            with col1:
                                new_is_active = st.checkbox(
                                    "Активен", value=criterion_data["is_active"]
                                )

                            with col2:
                                new_threshold = st.number_input(
                                    "Порог уверенности:",
                                    min_value=0.0,
                                    max_value=1.0,
                                    value=criterion_data["threshold"] or 0.5,
                                    step=0.1,
                                )

                            col1, col2, col3 = st.columns(3)

                            with col1:
                                update_submitted = st.form_submit_button("💾 Обновить")

                            with col2:
                                delete_submitted = st.form_submit_button("🗑️ Удалить")

                            with col3:
                                if st.form_submit_button("❌ Отмена"):
                                    st.session_state["show_edit_criterion"] = False
                                    st.rerun()

                            if update_submitted:
                                try:
                                    result = postgres_manager.update_criterion(
                                        criterion_id=criterion_id,
                                        criterion_text=new_criterion_text,
                                        is_active=new_is_active,
                                        threshold=new_threshold,
                                    )

                                    if result:
                                        st.success(
                                            f"✅ Критерий '{criterion_id}' успешно обновлен!"
                                        )
                                        st.session_state["show_edit_criterion"] = False
                                        st.rerun()
                                    else:
                                        st.error("❌ Ошибка при обновлении критерия")

                                except Exception as e:
                                    st.error(f"❌ Ошибка: {e}")

                            if delete_submitted:
                                try:
                                    # Подтверждение удаления
                                    if st.checkbox("Подтвердить удаление", key="confirm_delete"):
                                        result = postgres_manager.delete_criterion(criterion_id)

                                        if result:
                                            st.success(
                                                f"✅ Критерий '{criterion_id}' успешно удален!"
                                            )
                                            st.session_state["show_edit_criterion"] = False
                                            st.rerun()
                                        else:
                                            st.error("❌ Ошибка при удалении критерия")
                                    else:
                                        st.warning("⚠️ Подтвердите удаление, установив галочку")

                                except Exception as e:
                                    st.error(f"❌ Ошибка: {e}")
            else:
                st.info("📝 Нет критериев для редактирования")
                if st.button("❌ Отмена"):
                    st.session_state["show_edit_criterion"] = False
                    st.rerun()

    except Exception as e:
        st.error(f"❌ Ошибка загрузки критериев: {e}")
        st.exception(e)


if __name__ == "__main__":
    main()
