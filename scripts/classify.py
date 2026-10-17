import numpy as np,pickle
from sklearn.linear_model import LogisticRegression
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
M={0:62,1:64,2:57,3:61,4:60,5:59,6:36,7:56,8:63,9:52,10:53,11:9,12:50,13:48,14:54,15:64,16:17,17:41,18:49,19:57,20:42,21:34,22:29,23:51,24:43,25:31,26:20,27:61,28:38,29:63,
30:45,31:47,32:45,33:15,34:14,35:39,36:18,37:55,38:46,39:34,40:35,41:30,42:50,43:26,44:33,45:21,46:51,47:49,48:59,49:37,50:27,51:58,52:53,53:64,54:16,55:22,56:23,57:12,58:57,59:59,
60:25,61:56,62:31,63:10,64:60,65:43,66:24,67:35,68:64,69:11,70:62,71:61,72:63,73:64,74:18,75:52,76:40,77:7,78:28,79:41,80:23,81:29,82:44,83:52,84:20,85:6,86:64,87:1,88:63,89:15,
90:38,91:58,92:27,93:21,94:52,95:56,96:62,97:8,98:50,99:38,100:39,101:59,102:47,103:48,104:63,105:31,106:19,107:13,108:52,110:64,111:50,112:4,113:63,114:37,116:41,118:32,119:17}
SUB={1090:3,1091:5,1092:3,1150:40,1151:44,1152:2,1153:40,1170:33,1171:33,1172:33}
Z=np.load('Z.npy'); F=np.load('F.npy'); lab=np.load('km_lab.npy'); sub=np.load('sub.npy')
y0=np.array([M.get(k,-1) for k in lab]); m=sub>=0; y0[m]=[SUB[s] for s in sub[m]]
assert (y0>0).all(); assert set(y0)==set(range(1,65)), sorted(set(range(1,65))-set(y0))
X=np.hstack([Z,F]) if False else Z
y=y0.copy()
for it in range(3):
  clf=LinearDiscriminantAnalysis().fit(X,y)
  P=clf.predict_proba(X); yp=clf.classes_[P.argmax(1)]
  print('iter',it,'changed',(yp!=y).sum()); y=yp
srt=np.sort(P,1); conf=srt[:,-1]; margin=srt[:,-1]-srt[:,-2]
# also distance to own-class mean (outlier score) in LDA space
T=clf.transform(X); mu={c:T[y==c].mean(0) for c in clf.classes_}
d=np.array([np.linalg.norm(T[i]-mu[y[i]]) for i in range(len(y))])
dn=np.zeros_like(d)
for c in clf.classes_:
  s=y==c; dn[s]=d[s]/np.median(d[s])
np.savez('pred.npz',y=y,y0=y0,conf=conf,margin=margin,dn=dn,P2=clf.classes_[np.argsort(P,1)[:,-2]])
pickle.dump(clf,open('clf.pkl','wb'))
print('disagree with cluster labels',(y!=y0).sum())
