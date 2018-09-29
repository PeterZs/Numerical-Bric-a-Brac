"""
@author: Vincent Bonnet
@description : Constraint descriptions for implicit solver
"""

import numpy as np
import differentiation as diff

class BaseConstraint:
    '''
    Describes the constraint base
    '''
    def __init__(self, stiffness, damping, dynamics, particlesIds):
        N = len(particlesIds) # number of particles involved in the constraint
        self.stiffness = stiffness
        self.damping = damping
        self.f = np.zeros((N, 2))
        # Particle identifications
        self.localIds = np.copy(particlesIds) # local particle indices
        self.dynamicIndices = np.zeros(N, dtype=int) # indices of the dynamic objects
        self.globalIds = np.zeros(N, dtype=int)
        for i in range(N):
            self.dynamicIndices[i] = dynamics[i].index
            self.globalIds[i] = self.localIds[i] + dynamics[i].global_offset

        # Precomputed jacobians.
        # NxN matrix where each element is a 2x2 submatrix
        self.dfdx = np.zeros((N, N, 2, 2))
        self.dfdv = np.zeros((N, N, 2, 2))

    def applyForces(self, scene):
        for i in range(len(self.localIds)):
            dynamic = scene.dynamics[self.dynamicIndices[i]]
            dynamic.f[self.localIds[i]] += self.f[i]

    def computeForces(self, scene):
        raise NotImplementedError(type(self).__name__ + " needs to implement the method 'computeForces'")

    def computeJacobians(self, scene):
        raise NotImplementedError(type(self).__name__ + " needs to implement the method 'computeJacobians'")

    def getJacobianDx(self, fi, xj):
        return self.dfdx[fi][xj]

    def getJacobianDv(self, fi, xj):
        return self.dfdv[fi][xj]

class AnchorSpringConstraint(BaseConstraint):
    '''
    Describes a 2D spring constraint between a particle and point
    '''
    def __init__(self, stiffness, damping, dynamic, particleId, kinematic, pointParams):
        BaseConstraint.__init__(self, stiffness, damping, [dynamic], [particleId])
        targetPos = kinematic.getPointFromParametricValues(pointParams)
        self.restLength = np.linalg.norm(targetPos - dynamic.x[self.localIds[0]])
        self.pointParams = pointParams
        self.kinematicIndex = kinematic.index

    def getStates(self, scene):
        kinematic = scene.kinematics[self.kinematicIndex]
        dynamic = scene.dynamics[self.dynamicIndices[0]]
        x = dynamic.x[self.localIds[0]]
        v = dynamic.v[self.localIds[0]]
        return (kinematic, x, v)

    def computeForces(self, scene):
        kinematic, x, v = self.getStates(scene)
        targetPos = kinematic.getPointFromParametricValues(self.pointParams)
        # Numerical forces
        # f = -de/dx : the force is f,  e is the energy and x is the position
        #force = diff.numericalJacobian(elasticSpringEnergy, 0, x, targetPos, self.restLength, self.stiffness) * -1.0
        # Analytic forces
        force = springStretchForce(x, targetPos, self.restLength, self.stiffness)
        force += springDampingForce(x, targetPos, v, (0, 0), self.damping)
        # Set forces
        self.f[0] = force

    def computeJacobians(self, scene):
        kinematic, x, v = self.getStates(scene)
        targetPos = kinematic.getPointFromParametricValues(self.pointParams)
        # Numerical jacobians
        #dfdx = diff.numericalJacobian(springStretchForce, 0, x, targetPos, self.restLength, self.stiffness)
        #dfdv = diff.numericalJacobian(springDampingForce, 2, x, targetPos, v, (0,0), self.damping)
        # Analytic jacobians
        dfdx = springStretchJacobian(x, targetPos, self.restLength, self.stiffness)
        dfdv = springDampingJacobian(x, targetPos, v, (0, 0), self.damping)
        # Set jacobians
        self.dfdx[0][0] = dfdx
        self.dfdv[0][0] = dfdv

class SpringConstraint(BaseConstraint):
    '''
    Describes a 2D spring constraint between two particles
    '''
    def __init__(self, stiffness, damping, dynamics, particleIds):
        BaseConstraint.__init__(self, stiffness, damping, dynamics, particleIds)
        self.restLength = np.linalg.norm(dynamics[0].x[particleIds[0]] - dynamics[1].x[particleIds[1]])

    def getStates(self, scene):
        dynamic0 = scene.dynamics[self.dynamicIndices[0]]
        dynamic1 = scene.dynamics[self.dynamicIndices[1]]
        x0 = dynamic0.x[self.localIds[0]]
        x1 = dynamic1.x[self.localIds[1]]
        v0 = dynamic0.v[self.localIds[0]]
        v1 = dynamic1.v[self.localIds[1]]
        return (x0, x1, v0, v1)

    def computeForces(self, scene):
        x0, x1, v0, v1 = self.getStates(scene)
        # Numerical forces
        # f = -de/dx : the force is f,  e is the energy and x is the position
        #force = diff.numericalJacobian(elasticSpringEnergy, 0, x0, x1, self.restLength, self.stiffness) * -1.0
        # Analytic forces
        force = springStretchForce(x0, x1, self.restLength, self.stiffness)
        force += springDampingForce(x0, x1, v0, v1, self.damping)
        # Set forces
        self.f[0] = force
        self.f[1] = force * -1

    def computeJacobians(self, scene):
        x0, x1, v0, v1 = self.getStates(scene)
        # Numerical jacobians
        #dfdx = diff.numericalJacobian(springStretchForce, 0, x0, x1, self.restLength, self.stiffness)
        #dfdv = diff.numericalJacobian(springDampingForce, 2, x0, x1, v0, v1, self.damping)
        # Analytic jacobians
        dfdx = springStretchJacobian(x0, x1, self.restLength, self.stiffness)
        dfdv = springDampingJacobian(x0, x1, v0, v1, self.damping)
        # Set jacobians
        self.dfdx[0][0] = dfdx
        self.dfdx[1][1] = dfdx
        self.dfdx[0][1] = dfdx * -1
        self.dfdx[1][0] = dfdx * -1

        self.dfdv[0][0] = dfdv
        self.dfdv[1][1] = dfdv
        self.dfdv[0][1] = dfdv * -1
        self.dfdv[1][0] = dfdv * -1

class AreaConstraint(BaseConstraint):
    '''
    Describes a 2D area constraint between three particles
    '''
    def __init__(self, stiffness, damping, dynamics, particleIds):
        BaseConstraint.__init__(self, stiffness, damping, dynamics, particleIds)
        x0 = dynamics[0].x[particleIds[0]]
        x1 = dynamics[1].x[particleIds[1]]
        x2 = dynamics[2].x[particleIds[2]]
        v01 = np.subtract(x1, x0)
        v02 = np.subtract(x2, x0)
        self.restArea = np.abs(np.cross(v01, v02)) * 0.5

    def getStates(self, scene):
        dynamic0 = scene.dynamics[self.dynamicIndices[0]]
        dynamic1 = scene.dynamics[self.dynamicIndices[1]]
        dynamic2 = scene.dynamics[self.dynamicIndices[2]]
        x0 = dynamic0.x[self.localIds[0]]
        x1 = dynamic1.x[self.localIds[1]]
        x2 = dynamic2.x[self.localIds[2]]
        v0 = dynamic0.v[self.localIds[0]]
        v1 = dynamic1.v[self.localIds[1]]
        v2 = dynamic2.v[self.localIds[1]]
        return (x0, x1, x2, v0, v1, v2)

    def computeForces(self, scene):
        x0, x1, x2, v0, v1, v2 = self.getStates(scene)
        # Numerical forces
        force0 = diff.numericalJacobian(elasticAreaEnergy, 0, x0, x1, x2, self.restArea, self.stiffness) * -1.0
        force1 = diff.numericalJacobian(elasticAreaEnergy, 1, x0, x1, x2, self.restArea, self.stiffness) * -1.0
        force2 = diff.numericalJacobian(elasticAreaEnergy, 2, x0, x1, x2, self.restArea, self.stiffness) * -1.0
        # Analytic forces
        # TODO
        # Set forces
        self.f[0] = force0
        self.f[1] = force1
        self.f[2] = force2

    def computeJacobians(self, scene):
        x0, x1, x2, v0, v1, v2 = self.getStates(scene)
        # Numerical jacobians (Aka Hessian of the energy)
        dfdx00 = diff.numericalHessian(elasticAreaEnergy, 0, 0, x0, x1, x2, self.restArea, self.stiffness) * -1.0
        dfdx11 = diff.numericalHessian(elasticAreaEnergy, 1, 1, x0, x1, x2, self.restArea, self.stiffness) * -1.0
        dfdx22 = diff.numericalHessian(elasticAreaEnergy, 2, 2, x0, x1, x2, self.restArea, self.stiffness) * -1.0
        dfdx01 = diff.numericalHessian(elasticAreaEnergy, 0, 1, x0, x1, x2, self.restArea, self.stiffness) * -1.0
        dfdx02 = diff.numericalHessian(elasticAreaEnergy, 0, 2, x0, x1, x2, self.restArea, self.stiffness) * -1.0
        dfdx12 = diff.numericalHessian(elasticAreaEnergy, 1, 2, x0, x1, x2, self.restArea, self.stiffness) * -1.0
        # Analytic jacobians
        # TODO
        # Set jacobians
        self.dfdx[0][0] = dfdx00
        self.dfdx[1][1] = dfdx11
        self.dfdx[2][2] = dfdx22
        self.dfdx[0][1] = dfdx01
        self.dfdx[1][0] = dfdx01
        self.dfdx[0][2] = dfdx02
        self.dfdx[2][0] = dfdx02
        self.dfdx[1][2] = dfdx12
        self.dfdx[2][1] = dfdx12

class BendingConstraint(BaseConstraint):
    '''
    Describes a 2D bending constraint between three particles
    '''
    def __init__(self, stiffness, damping, dynamics, particleIds):
        BaseConstraint.__init__(self, stiffness, damping, dynamics, particleIds)
        # Constraint three points
        #  x0 -- x1 -- x2
        x0 = dynamics[0].x[particleIds[0]]
        x1 = dynamics[1].x[particleIds[1]]
        x2 = dynamics[2].x[particleIds[2]]
        self.restCurvature = computeCurvature(x0, x1, x2)

    def getStates(self, scene):
        dynamic0 = scene.dynamics[self.dynamicIndices[0]]
        dynamic1 = scene.dynamics[self.dynamicIndices[1]]
        dynamic2 = scene.dynamics[self.dynamicIndices[2]]
        x0 = dynamic0.x[self.localIds[0]]
        x1 = dynamic1.x[self.localIds[1]]
        x2 = dynamic2.x[self.localIds[2]]
        v0 = dynamic0.v[self.localIds[0]]
        v1 = dynamic1.v[self.localIds[1]]
        v2 = dynamic2.v[self.localIds[1]]
        return (x0, x1, x2, v0, v1, v2)

    def computeForces(self, scene):
        x0, x1, x2, v0, v1, v2 = self.getStates(scene)
        # Numerical forces
        force0 = diff.numericalJacobian(elasticBendingEnergy, 0, x0, x1, x2, self.restCurvature, self.stiffness) * -1.0
        force1 = diff.numericalJacobian(elasticBendingEnergy, 1, x0, x1, x2, self.restCurvature, self.stiffness) * -1.0
        force2 = diff.numericalJacobian(elasticBendingEnergy, 2, x0, x1, x2, self.restCurvature, self.stiffness) * -1.0
        # Analytic forces
        # TODO
        # Set forces
        self.f[0] = force0
        self.f[1] = force1
        self.f[2] = force2

    def computeJacobians(self, scene):
        x0, x1, x2, v0, v1, v2 = self.getStates(scene)
        # Numerical jacobians (Aka Hessian of the energy)
        dfdx00 = diff.numericalHessian(elasticBendingEnergy, 0, 0, x0, x1, x2, self.restCurvature, self.stiffness) * -1.0
        dfdx11 = diff.numericalHessian(elasticBendingEnergy, 1, 1, x0, x1, x2, self.restCurvature, self.stiffness) * -1.0
        dfdx22 = diff.numericalHessian(elasticBendingEnergy, 2, 2, x0, x1, x2, self.restCurvature, self.stiffness) * -1.0
        dfdx01 = diff.numericalHessian(elasticBendingEnergy, 0, 1, x0, x1, x2, self.restCurvature, self.stiffness) * -1.0
        dfdx02 = diff.numericalHessian(elasticBendingEnergy, 0, 2, x0, x1, x2, self.restCurvature, self.stiffness) * -1.0
        dfdx12 = diff.numericalHessian(elasticBendingEnergy, 1, 2, x0, x1, x2, self.restCurvature, self.stiffness) * -1.0
        # Analytic jacobians
        # TODO
        # Set jacobians
        self.dfdx[0][0] = dfdx00
        self.dfdx[1][1] = dfdx11
        self.dfdx[2][2] = dfdx22
        self.dfdx[0][1] = dfdx01
        self.dfdx[1][0] = dfdx01
        self.dfdx[0][2] = dfdx02
        self.dfdx[2][0] = dfdx02
        self.dfdx[1][2] = dfdx12
        self.dfdx[2][1] = dfdx12

'''
 Constraint Utility Functions
'''
# direction = normalized(x0-x1)
# stretch = norm(direction)
# A = outerProduct(direction, direction)
# I = identity matrix
# J =  -stiffness * [(1 - rest / stretch)(I - A) + A]
def springStretchJacobian(x0, x1, rest, stiffness):
    jacobian = np.zeros(shape=(2, 2))
    direction = x0 - x1
    stretch = np.linalg.norm(direction)
    I = np.identity(2)
    if not np.isclose(stretch, 0.0):
        direction /= stretch
        A = np.outer(direction, direction)
        jacobian = -1.0 * stiffness * ((1 - (rest / stretch)) * (I - A) + A)
    else:
        jacobian = -1.0 * stiffness * I

    return jacobian

def springDampingJacobian(x0, x1, v0, v1, damping):
    jacobian = np.zeros(shape=(2, 2))
    direction = x1 - x0
    stretch = np.linalg.norm(direction)
    if not np.isclose(stretch, 0.0):
        direction /= stretch
        A = np.outer(direction, direction)
        jacobian = -1.0 *damping * A

    return jacobian

def springStretchForce(x0, x1, rest, stiffness):
    direction = x1 - x0
    stretch = np.linalg.norm(direction)
    if not np.isclose(stretch, 0.0):
        direction /= stretch
    return direction * ((stretch - rest) * stiffness)

def springDampingForce(x0, x1, v0, v1, damping):
    direction = x1 - x0
    stretch = np.linalg.norm(direction)
    if not np.isclose(stretch, 0.0):
        direction /= stretch
    relativeVelocity = v1 - v0
    return direction * (np.dot(relativeVelocity, direction) * damping)

def elasticSpringEnergy(x0, x1, rest, stiffness):
    direction = x1 - x0
    stretch = np.linalg.norm(direction)
    return 0.5 * stiffness * ((stretch - rest) * (stretch - rest))

def elasticAreaEnergy(x0, x1, x2, restArea, stiffness):
    u = np.subtract(x1, x0)
    v = np.subtract(x2, x0)
    #area = np.abs(np.cross(u, v)) * 0.5 # expensive operation => replaced with line below
    area = np.abs(u[0]*v[1]-v[0]*u[1]) * 0.5
    return 0.5 * stiffness * ((area - restArea) * (area - restArea))

def computeCurvature(x0, x1, x2):
    '''
    Connect three points :
      x1
      /\
     /  \
    x0  x2
    Compute the curvature : |dT/ds| where T is the tangent and s the surface
    with
    t01 = x1 - x0 and t12 = x2 - x1
    mid01 = (x0 + x1) * 0.5
    mid12 = (x1 + x2) * 0.5
    discrete curvate formula 1: |t12 - t01| / |mid12 - mid01|
    discrete curvate formula 2: angle(t12,t01) / |mid12 - mid01|
    '''
    t01 = x1 - x0
    t01 /= np.linalg.norm(t01)
    t12 = x2 - x1
    t12 /= np.linalg.norm(t01)
    #mid01 = (x0 + x1) * 0.5
    #mid12 = (x1 + x2) * 0.5
    # Discrete curvature - poor (1)
    # curvature = np.linalg.norm([0,1]) / np.linalg.norm(mid12 - mid01)
    # Discrete curvature - accurate (2)
    det = t01[0]*t12[1] - t01[1]*t12[0]      # determinant
    dot = t01[0]*t12[0] + t01[1]*t12[1]      # dot product
    angle = np.math.atan2(det,dot)  # atan2 return range [-pi, pi]
    # TOFIX : instability to fix
    curvature = angle # / np.linalg.norm(mid12 - mid01)
    return curvature

def elasticBendingEnergy(x0, x1, x2, restCurvature, stiffness):
    curvature = computeCurvature(x0, x1, x2)
    #print(curvature - restCurvature)
    #curvature = restCurvature
    return 0.5 * stiffness * ((curvature - restCurvature) * (curvature - restCurvature))
