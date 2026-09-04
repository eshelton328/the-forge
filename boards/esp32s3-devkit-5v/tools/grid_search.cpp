// Bounded A* primitive. The Python caller supplies clearance-checked occupancy.
#include <queue>
#include <vector>
#include <cstdint>
#include <cmath>
#include <algorithm>
struct Item {float f;int id;bool operator<(const Item&o)const{return f>o.f;}};
extern "C" int find_path(int nx,int ny,int nl,const uint8_t*blocked,const uint8_t*via_ok,int start,int goal,int*output,int maxlen,int maxsteps){
 int area=nx*ny,N=area*nl;std::vector<float>dist(N,1e30f);std::vector<int>parent(N,-1);std::priority_queue<Item> q;
 int gx=goal%nx,gy=(goal%area)/nx,gl=goal/area;
 auto h=[&](int id){int x=id%nx,y=(id%area)/nx,l=id/area;int dx=abs(x-gx),dy=abs(y-gy);return float(std::max(dx,dy)+.414214*std::min(dx,dy)+(l!=gl?16:0));};
 dist[start]=0;q.push({h(start),start});int steps=0;
 int dxs[8]={1,-1,0,0,1,1,-1,-1},dys[8]={0,0,1,-1,1,-1,1,-1};
 while(!q.empty()&&++steps<maxsteps){auto cur=q.top();q.pop();int id=cur.id;if(cur.f>dist[id]+h(id)+.001f)continue;
 if(id==goal){std::vector<int> path;for(int j=id;j!=-1;j=parent[j])path.push_back(j);if(path.size()>maxlen)return -2;std::reverse(path.begin(),path.end());std::copy(path.begin(),path.end(),output);return path.size();}
 int x=id%nx,y=(id%area)/nx,l=id/area;
 for(int k=0;k<8;k++){int xx=x+dxs[k],yy=y+dys[k];if(xx<0||xx>=nx||yy<0||yy>=ny)continue;int nb=l*area+yy*nx+xx;if(blocked[nb])continue;
 if(k>=4&&(blocked[l*area+y*nx+xx]||blocked[l*area+yy*nx+x]))continue;
 float d=dist[id]+(k<4?1:1.414214f);if(l==1)d+=.02f;
 if(d<dist[nb]){dist[nb]=d;parent[nb]=id;q.push({d+h(nb),nb});}}
 if(via_ok[id%area])for(int ll=0;ll<nl;ll++){if(ll==l)continue;int nb=ll*area+id%area;if(blocked[nb])continue;float d=dist[id]+16;if(d<dist[nb]){dist[nb]=d;parent[nb]=id;q.push({d+h(nb),nb});}}
 }
 return 0;
}
