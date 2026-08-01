*** Intro
- https://rapids.ai/cudf-pandas/

// Read CSV
std::string filename = "/home/devavret/Development/1brc/data/measurements.txt";
cudf::io::csv_reader_options in_opts = 
    cudf::io::csv_reader_options::builder(cudf::io::source_info{filename})
      .delimiter(';')
      .dtypes(std::vector<cudf::data_type>{cudf::data_type{cudf::type_id::STRING},
                                             cudf::data_type{cudf::type_id::FLOAT32}})
      .na_filter(false);
auto result = cudf::io::read_csv(in_opts);

// Groupby and Aggregate
auto keys = result.tbl->select({0});
auto groupby_obj = cudf::groupby::groupby(keys);
std::vector<cudf::groupby::aggregation_request> aggregation_reqs{};
auto& req = aggregation_reqs.emplace_back();
req.values = result.tbl->get_column(1);
req.aggregations.emplace_back(cudf::make_min_aggregation<cudf::groupby_aggregation>());
req.aggregations.emplace_back(cudf::make_max_aggregation<cudf::groupby_aggregation>());
req.aggregations.emplace_back(cudf::make_mean_aggregation<cudf::groupby_aggregation>());
groupby_obj.aggregate(aggregation_reqs);


*** table_view and table

data buffer/ nullmask buffer
table_view支持选列



*** Note

- cuDF cannot handle > 2^31 chars.    ---> 不能GPU把数据一次全弄进一个data frame




*** 实现GroupBy

- row operators: https://docs.rapids.ai/api/libcudf/stable/row__operators_8cuh_source

struct row_comparator {
    row_comparator(table_device_view table) : table_(table) {}
    table_device_view table_;

    __device__ bool operator()(size_t lhs_index, size_t rhs_index) {
        auto state = EQUIVALENT;
        for (auto& col : table_) {
            auto col_comparison = col.compare(lhs_index, rhs_index);
            if (col_comparison == NOT_EQUIVALENT) {
                return false;
            } else if (col_comparison == EQUIVALENT) {
                continue;
            }
        }
        return true;
    }
};

struct row_hasher {
    row_hasher(table_device_view table) : table_(table) {}
    table_device_view table_;

    __device__ int64_t operator()(size_t index) {
        auto hash = SEED;
        for (auto& col : table_) {
            auto col_hash = hash_fn(col[index]);
            hash = hash_combine(hash, col_hash);
        }
        return hash; 
    }
};


*** gather

include/cudf/detail/gather.*

fixed width gather is available in thrust
