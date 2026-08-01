*** uvicorn

https://www.uvicorn.org/settings/


if __name__ == '__main__':
  uvicorn.run("autoops.api.app:app",
              host='0.0.0.0',
              port=int(args.port),
              workers=8,
              loop='uvloop')


*** click

@click.command()
@click.option('--file_path', type=click.Path(exists=True),
              help='Path to the parquet file')
def process_file(file_path):
    """
    Process the file specified by --file_path.
    """
    logger.info("Reading the parquet file {}...".format(file_path))

    dataset = CriteoParquetDataset(file_path)
    data_loader = DataLoader(dataset, batch_size=32, shuffle=False)
    for labels, dense, sparse in data_loader:
        logger.info("Labels: {}".format(labels))
        logger.info("Dense: {}".format(dense))
        logger.info("Sparse: {}".format(sparse))

        logger.info("Labels size and dtype: {}, {}".format(labels.size(), labels.dtype))
        logger.info("Dense size and dtype: {}, {}".format(dense.size(), dense.dtype))
        logger.info("Sparse size and dtype: {}, {}".format(sparse.size(), sparse.dtype))
        break


if __name__ == "__main__":
    process_file()