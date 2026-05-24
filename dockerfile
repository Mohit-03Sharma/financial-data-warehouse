FROM apache/airflow:2.8.0
RUN pip install \
    fredapi==0.5.2 \
    "multitasking==0.0.10" \
    "yfinance==0.2.33" \
    google-cloud-bigquery \
    google-cloud-storage \
    pandas \
    pyarrow \
    pandas-gbq \
    requests \
    lxml \
    html5lib