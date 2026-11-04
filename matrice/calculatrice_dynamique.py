from fractions import Fraction as F
def projection(qk,qj):
 x,y=F(qk),F(qj)
 return ((-3*x+2*y)/13,(2*x+3*y)/13)
def identification(q1,q2,dt):
 t=F(dt)
 if t<=0:raise ValueError("dt positif requis")
 a,b=projection(*q1);u,v=projection(*q2)
 e=a*a+b*b
 if e==0:raise ValueError("état nul : gamma/omega indéterminés")
 da,db=(u-a)/t,(v-b)/t
 gamma=-(a*da+b*db)/e
 omega=(a*db-b*da)/e
 assert -gamma*a-omega*b==da
 assert omega*a-gamma*b==db
 return {"gamma":str(gamma),"omega":str(omega),"E":str(e),
         "identification_locale":True,"prediction_validee":False}
