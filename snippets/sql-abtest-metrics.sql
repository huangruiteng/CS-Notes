-- ********************************************************************
-- Author: YOUR_NAME
-- Description: AB实验指标统计脚本 (通用模板)
-- ********************************************************************

-- 配置 Catalog (按需调整)
-- set spark.sql.catalog.paimon=org.apache.paimon.spark.SparkCatalog;
-- set spark.sql.catalog.paimon.warehouse=tos://YOUR_BUCKET/lakehouse;

WITH api AS (
    SELECT  get_json_object(api_request, '$.user._user_id') AS user_id,
            get_json_object(api_request, '$._abtest_vid') AS vid,
            get_json_object(api_request, '$.event_scene') AS scene,
            MIN(request_timestamp) AS ts
    FROM    `your_catalog`.`your_database`.`your_api_log_table`
    WHERE   date >= '${start_date}'
    AND     account_id = '${account_id}'
    AND     application_id = '${app_id}'
    AND     api_request IS NOT NULL
    AND     get_json_object(api_request, '$.event_scene') = '${target_scene}'
    GROUP BY
            get_json_object(api_request, '$.user._user_id'),
            get_json_object(api_request, '$._abtest_vid'),
            get_json_object(api_request, '$.event_scene')
),
base AS (
    SELECT  get_json_object(data, '$.event_scene') AS event_scene,
            get_json_object(data, '$.event_type') AS event_type,
            get_json_object(data, '$.event_timestamp') AS event_timestamp,
            get_json_object(data, '$.user_id') AS user_id,
            get_json_object(data, '$.item_id') AS item_id,
            get_json_object(data, '$.scm') AS scm
    FROM    `your_catalog`.`your_database`.`your_behavior_log_table`
    WHERE   date >= '${start_date}'
    AND     _dataset_id = ${dataset_id}
    AND     get_json_object(data, '$.scm') = '${target_scm}'
    AND     get_json_object(data, '$.event_scene') = '${target_scene}'
),
user_stats AS (
    SELECT  b.user_id,
            b.event_scene,
            a.vid,
            SUM(IF(event_type = 'click_event', 1, 0)) AS click_cnt,
            SUM(IF(event_type = 'like_event', 1, 0)) AS like_cnt,
            SUM(IF(event_type = 'show_event', 1, 0)) AS exposure_cnt
    FROM    base b
    JOIN    api a
    ON      b.user_id = a.user_id
    -- 归因逻辑: 
    -- 1. 行为发生在 API 请求之后 (b.timestamp > a.ts)
    -- 2. 限制归因窗口 (如 1 小时内)，避免跨越扩缩量周期的错误归因
    AND     b.event_timestamp > a.ts
    AND     b.event_timestamp <= a.ts + 3600 * 1000
    AND     b.event_scene = a.scene
    GROUP BY
            b.user_id,
            b.event_scene,
            a.vid
),
user_stats_with_total AS (
    SELECT  *,
            -- 计算用户在所有事件下的总点击数，用于判断是否为异常用户
            SUM(click_cnt) OVER (PARTITION BY user_id) AS total_user_clicks
    FROM    user_stats
)
SELECT  vid,
        count(DISTINCT user_id) AS user_cnt,
        -- 原始 CTR
        SUM(click_cnt) / SUM(exposure_cnt) AS pv_ctr,
        
        -- 策略1: 截断 (Capping)
        -- 单个用户在单个事件上的点击数超过 N 则按 N 计算，然后再聚合
        SUM(LEAST(click_cnt, 50)) / SUM(exposure_cnt) AS pv_ctr_capped,
        
        -- 策略2: 剔除 (Filtering)
        -- 直接剔除总点击数超过 M 的异常用户（爬虫/刷量）
        SUM(IF(total_user_clicks > 200, 0, click_cnt)) / SUM(IF(total_user_clicks > 200, 0, exposure_cnt)) AS pv_ctr_filtered,
        
        count(distinct if(click_cnt > 0, user_id, null)) / count(distinct if(exposure_cnt > 0, user_id, null)) AS uv_ctr,
        SUM(exposure_cnt) / count(DISTINCT user_id) AS exposure_perU,
        SUM(click_cnt) / count(DISTINCT user_id) AS click_perU,
        SUM(like_cnt) / count(DISTINCT user_id) AS like_perU,
        SUM(exposure_cnt) AS total_exposure,
        SUM(click_cnt) AS total_click,
        SUM(like_cnt) AS total_like
FROM    user_stats_with_total
GROUP BY
        vid
ORDER BY
        vid
