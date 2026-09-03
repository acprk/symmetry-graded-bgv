// Census with an early-exit test. A member fails the norm criterion as soon as it has an
// irreducible factor of degree not divisible by d; testing k=1 alone (a single gcd with
// x^p - x) rejects the majority of members, and rejects every member of an obstructed
// coset immediately. Survivors go through the full distinct-degree factorisation.
#include <NTL/ZZ_pX.h>
#include <NTL/ZZ_pXFactoring.h>
#include <cstdio>
#include <cstdlib>
#include <map>
#include <vector>
using namespace NTL; using namespace std;
int main(int argc, char** argv) {
  long p=atol(argv[1]), A=atol(argv[2]), B=atol(argv[3]), hex=atol(argv[4]);
  vector<long> rs, ds;
  { const char* s=argv[5]; long v=0; for(const char* q=s;;q++){ if(*q>='0'&&*q<='9')v=v*10+(*q-'0');
      else{ if(v)rs.push_back(v); v=0; if(!*q)break; } } }
  { const char* s=argv[6]; long v=0; for(const char* q=s;;q++){ if(*q>='0'&&*q<='9')v=v*10+(*q-'0');
      else{ if(v)ds.push_back(v); v=0; if(!*q)break; } } }
  ZZ_p::init(conv<ZZ>(p));
  printf("# census2 p=%ld A=%ld B=%ld %s\n",p,A,B,hex?"hexagon":"box");
  printf("# %-3s %-6s %-4s %-8s %-8s %-8s %s\n","r","n'","d","scanned","IRR","NORM","gcd(Q,G)");
  fflush(stdout);
  for (long r : rs) {
    map<long,long> low; bool ok=true;
    for(long e=-B;e<=B&&ok;e++)for(long l=-B;l<=B&&ok;l++){
      if(hex&&labs(e+l)>B)continue;
      long x=((((e%p)*(A%p))%p+(l%p))%p+p)%p, lv=((l%p)+p)%p;
      auto it=low.find(x); if(it!=low.end()&&it->second!=lv)ok=false; else low[x]=lv; }
    if(!ok){printf("  r=%ld not injective\n",r);continue;}
    long A2=MulMod(A%p,A%p,p),den=((1-A2)%p+p)%p;
    long c1=(r>=3&&den)?InvMod(den,p):0,u=r-1;
    map<long,long> qv;
    for(auto&kv:low){ long x=kv.first,lv=kv.second; if(!x)continue;
      long y=PowerMod(x,r,p);
      long vv=MulMod(SubMod(lv,MulMod(x,c1,p),p),InvMod(PowerMod(x,u,p),p),p);
      auto jt=qv.find(y); if(jt!=qv.end()&&jt->second!=vv){ok=false;break;} qv[y]=vv; }
    if(!ok){printf("  r=%ld fold inconsistent\n",r);continue;}
    long n=qv.size();
    vec_ZZ_p xs,ys; xs.SetLength(n); ys.SetLength(n);
    { long i=0; for(auto&kv:qv){xs[i]=conv<ZZ_p>(kv.first);ys[i]=conv<ZZ_p>(kv.second);i++;} }
    ZZ_pX Q=interpolate(xs,ys),G0; BuildFromRoots(G0,xs);
    long dg=deg(GCD(Q,G0));
    for (long d : ds) {
      long np=((n+d-1)/d)*d;
      ZZ_pX G=G0; { long extra=np-n,cand=1;
        while(extra>0){ if(!qv.count(cand)){ ZZ_pX lin; SetX(lin); lin-=conv<ZZ_p>(cand); G*=lin; extra--; } cand++; } }
      long nIrr=0,nNorm=0,scanned=0;
      ZZ_pX Xpoly; SetX(Xpoly);
      for(long c=1;c<p;c++){
        ZZ_pX F=Q+conv<ZZ_p>(c)*G; if(deg(F)!=np)continue;
        MakeMonic(F); scanned++;
        if(deg(GCD(F,diff(F)))!=0)continue;                  // squarefree
        ZZ_pX h=PowerXMod(ZZ_p::modulus(),F);
        if(d>1 && deg(GCD(F,h-Xpoly))>0) continue;           // early exit: linear factor
        vec_pair_ZZ_pX_long fac; DDF(fac,F,h,0);
        bool norm=true,irr=false;
        for(long i=0;i<fac.length();i++){
          if(deg(fac[i].a)==0)continue;
          if(fac[i].b%d!=0){norm=false;break;}
          if(fac[i].b==np)irr=true; }
        if(norm)nNorm++; if(irr)nIrr++;
      }
      printf("  %-3ld %-6ld %-4ld %-8ld %-8ld %-8ld %ld\n",r,np,d,scanned,nIrr,nNorm,dg);
      fflush(stdout);
    }
  }
  return 0;
}
