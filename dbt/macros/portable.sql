{% macro json_text(column, path) -%}
  {% if target.type == 'bigquery' %}json_value({{ column }}, '{{ path }}')
  {% elif target.type == 'databricks' %}get_json_object({{ column }}, '{{ path }}')
  {% else %}json_extract_string({{ column }}, '{{ path }}'){% endif %}
{%- endmacro %}

{% macro json_string_array(column, path) -%}
  {% if target.type == 'bigquery' %}
    coalesce(json_value_array({{ column }}, '{{ path }}'), cast([] as array<string>))
  {% elif target.type == 'databricks' %}
    coalesce(from_json(get_json_object({{ column }}, '{{ path }}'), 'ARRAY<STRING>'), cast(array() as array<string>))
  {% else %}
    coalesce(from_json(json_extract({{ column }}, '{{ path }}'), '["VARCHAR"]'), []::varchar[])
  {% endif %}
{%- endmacro %}

{% macro unnest_locations(column) -%}
  {% if target.type == 'bigquery' %}cross join unnest({{ column }}) as location_value
  {% elif target.type == 'databricks' %}lateral view explode({{ column }}) locations as location_value
  {% else %}cross join unnest({{ column }}) as locations(location_value){% endif %}
{%- endmacro %}

{% macro matches(value, pattern) -%}
  {% if target.type == 'bigquery' %}regexp_contains({{ value }}, {{ pattern }})
  {% elif target.type == 'databricks' %}regexp_like({{ value }}, {{ pattern }})
  {% else %}regexp_matches({{ value }}, {{ pattern }}){% endif %}
{%- endmacro %}

{% macro daily_table(clusters=[]) %}
  {% if target.type == 'bigquery' %}
    {{ config(partition_by={'field': 'snapshot_date', 'data_type': 'date'}, cluster_by=clusters) }}
  {% endif %}
{% endmacro %}
