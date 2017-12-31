def batch_iterator(iterable, batch_size):
    iterator = iter(iterable)
    iteration_stopped = False

    while True:
        batch = []
        for _ in range(batch_size):
            try:
                batch.append(next(iterator))
            except StopIteration:
                iteration_stopped = True
                break

        yield batch
        if iteration_stopped:
            break
