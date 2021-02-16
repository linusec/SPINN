# Poisson equation on a general domain

import numpy as np
from mayavi import mlab
from common import PDE, tensor
from spinn2d import Problem2D, App2D, SPINN2D

class Poisson2D(PDE):
    @classmethod
    def from_args(cls, args):
        return cls(args.f_nodes_int, args.f_nodes_bdy, args.f_samples_int, args.f_samples_bdy)

    @classmethod
    def setup_argparse(cls, parser, **kw):
        p = parser
        p.add_argument(
            '--f_nodes_int', '-ni', dest='f_nodes_int',
            default=kw.get('f_nodes_int', 'mesh_data/interior_nodes.dat'), type=str,
            help='File containing interior nodes.'
        )
        p.add_argument(
            '--f_nodes_bdy', '-nb', dest='f_nodes_bdy',
            default=kw.get('f_nodes_bdy', 'mesh_data/boundary_nodes.dat'), type=str,
            help='File containing boundary nodes.'
        )
        p.add_argument(
            '--f_samples_int', '-si', dest='f_samples_int',
            default=kw.get('f_samples_int', 'mesh_data/interior_samples.dat'), type=str,
            help='File containing interior samples.'
        )
        p.add_argument(
            '--f_samples_bdy', '-sb', dest='f_samples_bdy',
            default=kw.get('f_samples_bdy', 'mesh_data/boundary_samples.dat'), type=str,
            help='File containing boundary samples.'
        )

    def _extract_coordinates(self, f_pts):
        xs = []
        ys = []

        with open(f_pts, 'r') as f:
            line = f.readline()
            words = line.split()
            n = int(words[0])

            for _ in range(n):
                line = f.readline()
                words = line.split()
                xs.append(float(words[0]))
                ys.append(float(words[1]))

        return np.asarray(xs), np.asarray(ys)

    def __init__(self,
        f_nodes_int, f_nodes_bdy,
        f_samples_int, f_samples_bdy):

        self.f_nodes_int = f_nodes_int
        self.f_nodes_bdy = f_nodes_bdy

        self.f_samples_int = f_samples_int
        self.f_samples_bdy = f_samples_bdy

        # Interior nodes: Free
        xi, yi = self._extract_coordinates(f_nodes_int)
        self.interior_nodes = (xi, yi)

        ## Boundary nodes: Fixed
        xb, yb = self._extract_coordinates(f_nodes_bdy)
        self.boundary_nodes = (xb, yb)

        ## Interior samples
        xi, yi = self._extract_coordinates(f_samples_int)
        self.interior_samples = (tensor(xi, requires_grad=True),
                                 tensor(yi, requires_grad=True))

        ## Boundary samples
        xb, yb = self._extract_coordinates(f_samples_bdy)
        self.boundary_samples = (tensor(xb, requires_grad=True),
                                 tensor(yb, requires_grad=True))
        
    def nodes(self):
        return self.interior_nodes

    def fixed_nodes(self):
        return self.boundary_nodes

    def interior(self):
        return self.interior_samples

    def boundary(self):
        return self.boundary_samples

    def plot_points(self):
        xi, yi = self._extract_coordinates(self.f_samples_int)
        return (tensor(xi), tensor(yi))

    def eval_bc(self, problem):
        xb, tb = self.boundary()
        u = problem.nn(xb, tb)
        ub = 0.0
        return u - ub

    def pde(self, x, y, u, ux, uy, uxx, uyy):
        return uxx + uyy + 1.0

    def has_exact(self):
        return False

class PoissonProblem(Problem2D):
    def get_plot_data(self):
        x, y = self.pde.plot_points()
        pn = self.nn(x, y).detach().cpu().numpy()
        pn.shape = x.shape
        xn = x.detach().cpu().numpy()
        yn = y.detach().cpu().numpy()
        return xn, yn, pn

    def plot_solution(self):
        xn, yn, pn = self.get_plot_data()
        pde = self.pde
        if self.plt1 is None:
            mlab.figure(size=(700, 700))
            self.plt1 = mlab.points3d(xn, yn, pn, pn)
        else:
            self.plt1.mlab_source.scalars = pn
        return self.get_error(xn, yn, pn)

if __name__ == '__main__':
    app = App2D(
        problem_cls=PoissonProblem,
        nn_cls=SPINN2D,
        pde_cls=Poisson2D
    )
    app.run(lr=1e-2)
