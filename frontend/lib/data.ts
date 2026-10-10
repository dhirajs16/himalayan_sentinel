import type { Region } from "./types";
const raw = [
 ["rasuwa","Rasuwa","Bagmati","Bhotekoshi–Trishuli",28.156,85.329,132,"Rising rapidly","Very high",8,18400,[52,58,61,68,73,79,84],[38,45,62,88,96,118,132],[88,82,92,64,58]],
 ["sindhupalchok","Sindhupalchok","Bagmati","Bhotekoshi–Sunkoshi",27.951,85.684,118,"Above alert threshold","High",11,32600,[48,55,59,64,70,75,79],[34,49,55,72,91,105,118],[78.7,78,72,76,74]],
 ["solukhumbu","Solukhumbu","Koshi","Dudh Koshi",27.793,86.71,86,"Elevated","Very high",5,9200,[42,46,51,55,62,66,69],[22,31,38,52,61,73,86],[57.3,62,88,42,44]],
 ["dolakha","Dolakha","Bagmati","Tamakoshi",27.778,86.175,96,"Elevated","High",6,15100,[39,44,48,54,59,64,70],[27,36,44,58,71,84,96],[64,65,79,50,56]],
 ["mustang","Mustang","Gandaki","Kali Gandaki",28.999,83.848,34,"Normal","High",2,4100,[28,31,33,35,38,40,42],[8,12,15,19,23,28,34],[22.7,35,63,24,22]],
 ["manang","Manang","Gandaki","Marsyangdi",28.667,84.017,48,"Watch","High",3,3600,[31,35,38,42,46,49,52],[11,17,22,28,33,41,48],[32,48,67,32,20]],
 ["sankhuwasabha","Sankhuwasabha","Koshi","Arun",27.357,87.149,104,"Elevated","Moderate",4,12400,[37,43,48,53,57,61,65],[29,41,50,66,78,92,104],[69.3,68,58,45,48]],
 ["taplejung","Taplejung","Koshi","Tamor",27.354,87.668,76,"Watch","High",2,7800,[29,33,38,43,47,51,55],[18,25,31,43,52,64,76],[50.7,54,61,20,38]]
] as const;
const level=(s:number)=>s>75?"Critical":s>50?"High":s>25?"Moderate":"Low";
export const fallbackRegions:Region[]=raw.map(r=>{const f={rainfall_score:r[13][0],river_level_score:r[13][1],glacial_risk_score:r[13][2],community_report_score:r[13][3],population_exposure_score:r[13][4]};const score=+(f.rainfall_score*.3+f.river_level_score*.25+f.glacial_risk_score*.2+f.community_report_score*.15+f.population_exposure_score*.1).toFixed(1);return {id:r[0],name:r[1],province:r[2],basin:r[3],lat:r[4],lng:r[5],rainfall_mm:r[6],river_status:r[7],glacial_risk:r[8],reports:r[9],population_exposed:r[10],trend:[...r[11]],rainfall_trend:[...r[12]],risk:{score,level:level(score),factors:f,weights:{rainfall_score:.3,river_level_score:.25,glacial_risk_score:.2,community_report_score:.15,population_exposure_score:.1}}} as Region});
