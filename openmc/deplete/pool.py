"""Dedicated module containing depletion function

Provided to avoid some circular imports
"""
from itertools import repeat, starmap
from multiprocessing import Pool


# Configurable switch that enables / disables the use of
# multiprocessing routines during depletion
USE_MULTIPROCESSING = True

# Allow user to override the number of worker processes to use for depletion
# calculations
NUM_PROCESSES = None


def deplete(func, chain, x, rates, dt, msr, matrix_func=None):
    """Deplete materials using given reaction rates for a specified time

    Parameters
    ----------
    func : callable
        Function to use to get new compositions. Expected to have the
        signature ``func(A, n0, t) -> n1``
    chain : openmc.deplete.Chain
        Depletion chain
    x : list of numpy.ndarray
        Atom number vectors for each material
    rates : openmc.deplete.ReactionRates
        Reaction rates (from transport operator)
    dt : float
        Time in [s] to deplete for
    msr : openmc.deplete.MsrContinuous, Optional
        MsrContinuous removal terms to add to Bateman equation,
        accounting for material transfers.
    maxtrix_func : callable, optional
        Function to form the depletion matrix after calling
        ``matrix_func(chain, rates, fission_yields)``, where
        ``fission_yields = {parent: {product: yield_frac}}``
        Expected to return the depletion matrix required by
        ``func``

    Returns
    -------
    x_result : list of numpy.ndarray
        Updated atom number vectors for each material

    """
    
    fission_yields = chain.fission_yields
    if len(fission_yields) == 1:
        fission_yields = repeat(fission_yields[0])
    elif len(fission_yields) != len(x):
        raise ValueError(
            "Number of material fission yield distributions {} is not "
            "equal to the number of compositions {}".format(
                len(fission_yields), len(x)))

    # Unzip rates from high orders integrator schemes (such as CF4Integrator)
    if type(rates) is list:
        rate = list(zip(*rates))[0][0]
        list_rates = deepcopy(rates)
    else:
        rate = rates[0]
        list_rates = list(deepcopy(rates))

    # Create dictionary of depletable materials indeces
    depletable_ids = {int(k): v for k, v in rate.index_mat.items()}

    # Create null dictionary with repeated depletable materials indeces for
    # sparse matrix contstruction
    sparse_ids = {(i, i): None for i in range(rate.n_mat)}

    if msr is None:
        if matrix_func is None:
            matrices = map(chain.form_matrix, rates, sparse_ids.items(),
                           fission_yields)
        else:
            matrices = map(matrix_func, repeat(chain), rates,
                           sparse_ids.items(), fission_yields)
        inputs = zip(matrices, x, repeat(dt))
        if USE_MULTIPROCESSING:
            with Pool() as pool:
                x_result = list(pool.starmap(func, inputs))
        else:
            x_result = list(starmap(func, inputs))

    else:
        fission_yields = deepcopy(fission_yields)
        # Create zero reactio rates to be added to off-diagonal terms
        null_rate = rate.copy()
        null_rate.fill(0.0)
        null_fy = deepcopy(fission_yields[0])
        for product, y in null_fy.items():
            y.yields.fill(0.0)

        # Assign lambda coefficients instructions to dictionary and add
        # off-diagonal terms
        for r in msr:
            j = depletable_ids[r['mat_id']]
            sparse_ids[(j, j)] = r['transfer']
            for t in r['transfer']:
                if type(rates) is list:
                    list_rates.append((null_rate,)*len(list(zip(*rates))))
                else:
                    list_rates.append(null_rate)
                fission_yields.append(null_fy)
                i = depletable_ids[t['to']]
                sparse_ids[(i, j)] = t

        # Form all the matrices
        if matrix_func is None:
            matrices = map(chain.form_matrix, list_rates,
                           sparse_ids.items(), fission_yields)
        else:
            matrices = map(matrix_func, repeat(chain), list_rates,
                           sparse_ids.items(), fission_yields)

        # Create a 2d array with all the matrices coefficients
        matrices = list(matrices)
        raws = []
        for raw in range(rate.n_mat):
            cols = []
            for col in range(rate.n_mat):
                val = None
                for keys, array in zip(sparse_ids.keys(), matrices):
                    if keys == (raw,col):
                        val = array
                cols.append(val)
            raws.append(cols)

        # Build a sparse matrix from the sparse sub-arrays
        sparse = bmat(raws)

        # Concatenate all atoms vectors in one
        x = np.concatenate([xx for xx in x])

        x_result = func(sparse, x, dt)

        # Split back the atoms vectors before returning
        split = np.cumsum([i.shape[0] for i in matrices[:rate.n_mat]])
        x_result = np.split(x_result, split.tolist()[:-1])

    return x_result
