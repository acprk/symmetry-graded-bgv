// Verify the obstruction theorem: gcd(Q, Gamma) over F_p for each filter order r.
// Prediction: r=2 (c1=0) -> gcd degree ~B (fixed linear factors at the lambda=0 points),
//             r=3,6 (c1!=0) -> gcd degree 0 under B-injectivity.
#include <NTL/ZZ_pX.h>
#include <cstdio>
#include <cstdlib>
#include <map>
using namespace NTL; using namespace std;
int main(int argc,char**argv){
  long p=atol(argv[1]),A=atol(argv[2]),B=atol(argv[3]),hex=atol(argv[4]);
  ZZ_p::init(conv<ZZ>(p));
  printf("p=%ld A=%ld B=%ld %s\n",p,A,B,hex?"hexagon":"box");
  long rs[3]={2,3,6};
  for(int t=0;t<3;t++){long r=rs[t];
    map<long,long> low; bool ok=true;
    for(long e=-B;e<=B&&ok;e++)for(long l=-B;l<=B&&ok;l++){
      if(hex&&labs(e+l)>B)continue;
      long x=((((e%p)*(A%p))%p+(l%p))%p+p)%p, lv=((l%p)+p)%p;
      auto it=low.find(x); if(it!=low.end()&&it->second!=lv)ok=false; else low[x]=lv;}
    if(!ok){printf("r=%ld not injective\n",r);continue;}
    long A2=MulMod(A%p,A%p,p),den=((1-A2)%p+p)%p;
    long c1=(r>=3&&den)?InvMod(den,p):0,u=r-1;
    map<long,long> qv; long zeros=0;
    for(auto&kv:low){long x=kv.first,lv=kv.second; if(!x)continue;
      long y=PowerMod(x,r,p);
      long v=MulMod(SubMod(lv,MulMod(x,c1,p),p),InvMod(PowerMod(x,u,p),p),p);
      if(v==0)zeros++;
      auto jt=qv.find(y); if(jt!=qv.end()&&jt->second!=v){ok=false;break;} qv[y]=v;}
    if(!ok){printf("r=%ld inconsistent\n",r);continue;}
    long n=qv.size();
    vec_ZZ_p xs,ys; xs.SetLength(n); ys.SetLength(n); long i=0;
    for(auto&kv:qv){xs[i]=conv<ZZ_p>(kv.first);ys[i]=conv<ZZ_p>(kv.second);i++;}
    ZZ_pX Q=interpolate(xs,ys),G; BuildFromRoots(G,xs);
    ZZ_pX g=GCD(Q,G);
    printf("r=%ld  c1=%ld  |folded|=%ld  Q-zeros-on-support=%ld  deg gcd(Q,Gamma)=%ld\n",
           r,c1,n,zeros,(long)deg(g));
  }
  return 0;
}
