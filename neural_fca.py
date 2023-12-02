import logging

import numpy as np
from sklearn.metrics import f1_score

from fcapy.context import FormalContext
from fcapy.lattice import ConceptLattice

import neural_lib as nl

logger = logging.getLogger(__name__)

class NeuralFCA():
    def __init__(self, best_concepts_fraction=0.5) -> None:
        self.best_concepts_fraction=best_concepts_fraction
        self.cn : nl.ConceptNetwork = None

    def fit(self, X_train, y_train):
        logger.info("Constructing formal context..")
        K_train = FormalContext.from_pandas(X_train)
        # attribute_names = [ str(n) for n in list(range(len(X_train.columns))) ]
        # K_train = FormalContext(data=X_train.values, target=y_train.astype(int).values, attribute_names=)

        logger.info("Constructing concept lattice..")
        L = ConceptLattice.from_context(K_train, is_monotone=True, algo='Sofia')
        for c in L:
            y_preds = np.zeros(K_train.n_objects)
            y_preds[list(c.extent_i)] = 1
            c.measures['f1_score'] = f1_score(y_train, y_preds)

        n_concepts = len(list(L.measures['f1_score'].argsort()[::-1]))
        n_best_concepts = int(n_concepts * self.best_concepts_fraction)
        best_concepts = list(L.measures['f1_score'].argsort()[::-1][:n_best_concepts])
        assert len({g_i for c in L[best_concepts] for g_i in c.extent_i})==K_train.n_objects, "Selected concepts do not cover all train objects"

        logger.info("Fitting concept network..")
        self.cn = nl.ConceptNetwork.from_lattice(L, best_concepts, sorted(set(y_train)))
        self.cn.fit(X_train, y_train)
        return self
    
    def score(self, X, y):
        assert self.cn, "Concept network is not fitted"
        return f1_score(y, self.cn.predict(X))
