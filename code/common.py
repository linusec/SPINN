import os
import time

import numpy as np
import torch.optim as optim


class DiffEq:
    def ode(self, x, u, ux, uxx):
        pass

    def exact(self, *args):
        pass


class Case:
    @classmethod
    def from_args(cls, nn, args):
        pass

    @classmethod
    def setup_argparse(cls, parser, **kw):
        pass

    def loss(self):
        '''Return the loss.
        '''
        raise NotImplementedError()

    def get_plot_data(self):
        pass

    def get_error(self, **kw):
        pass

    def plot_solution(self):
        pass

    def plot(self):
        pass

    def plot_weights(self):
        '''Implement this method to plot any weights.
        Note this is always called *after* plot_solution.
        '''
        pass

    def save(self, dirname):
        '''Save the model and results.

        '''
        pass

    def show(self):
        pass


class Solver:
    @classmethod
    def from_args(cls, case, args):
        optimizers = {'Adam': optim.Adam, 'LBFGS': optim.LBFGS}
        o = optimizers[args.optimizer]
        return cls(
            case, n_train=args.n_train,
            n_skip=args.n_skip, lr=args.lr, plot=args.plot,
            out_dir=args.directory, opt_class=o
        )

    @classmethod
    def setup_argparse(cls, parser, **kw):
        p = parser
        p.add_argument(
            '--n-train', '-t', dest='n_train',
            default=kw.get('n_train', 2500), type=int,
            help='Number of training iterations.'
        )
        p.add_argument(
            '--n-skip', dest='n_skip',
            default=kw.get('n_skip', 100), type=int,
            help='Number of iterations after which we print/update plots.'
        )
        p.add_argument(
            '--plot', dest='plot', action='store_true', default=False,
            help='Show a live plot of the results.'
        )
        p.add_argument(
            '--lr', dest='lr', default=kw.get('lr', 1e-2), type=float,
            help='Learning rate.'
        )
        p.add_argument(
            '--optimizer', dest='optimizer',
            default=kw.get('optimizer', 'Adam'),
            choices=['Adam', 'LBFGS'], help='Optimizer to use.'
        )
        p.add_argument(
            '-d', '--directory', dest='directory',
            default=kw.get('directory', None),
            help='Output directory (output files are dumped here).'
        )

    def __init__(self, case, n_train, n_skip=100, lr=1e-2, plot=True,
                 out_dir=None, opt_class=optim.Adam):
        '''Initializer

        Parameters
        -----------

        case: Case: The problem case being solved.
        n_train: int: Training steps
        n_skip: int: Print loss every so often.
        lr: float: Learming rate
        plot: bool: Plot live solution.
        out_dir: str: Output directory.
        '''
        self.case = case
        self.opt_class = opt_class
        self.errors = []
        self.loss = []
        self.time_taken = 0.0
        self.n_train = n_train
        self.n_skip = n_skip
        self.lr = lr
        self.plot = plot
        self.out_dir = out_dir

    def closure(self):
        opt = self.opt
        opt.zero_grad()
        loss = self.case.loss()
        loss.backward()
        self.loss.append(loss.item())
        return loss

    def solve(self):
        case = self.case
        n_train = self.n_train
        n_skip = self.n_skip
        opt = self.opt_class(case.nn.parameters(), lr=self.lr)
        self.opt = opt
        if self.plot:
            case.plot()

        start = time.perf_counter()
        for i in range(1, n_train+1):
            opt.step(self.closure)
            if i % n_skip == 0 or i == n_train:
                loss = self.case.loss()
                err = 0.0
                if self.plot:
                    err = case.plot()
                else:
                    err = case.get_error()
                self.errors.append(err)
                print(
                    f"Iteration ({i}/{n_train}): Loss={loss:.3e}, " +
                    f"error={err:.3e}"
                )
        time_taken = time.perf_counter() - start
        self.time_taken = time_taken
        print(f"Done. Took {time_taken:.3f} seconds.")
        if self.plot:
            case.show()

    def save(self):
        dirname = self.out_dir
        if self.out_dir is None:
            print("No output directory set.  Skipping.")
            return
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        print("Saving output to", dirname)
        fname = os.path.join(dirname, 'solver.npz')
        np.savez(
            fname, loss=self.loss, error=self.errors,
            time_taken=self.time_taken
        )
        self.case.save(dirname)