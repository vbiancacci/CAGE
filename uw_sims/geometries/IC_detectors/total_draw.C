void total_draw()
// Example simple postprocessing in root: plot spectra of total Edep (>0) in each TubeVol 
{
  //gStyle->SetOptStat(0);
  //gStyle->SetOptTitle(0);

  TFile* file = TFile::Open("total_out.root");
  
  TCanvas* c1 = new TCanvas("c1","c1", 0,0,900,800);	
  c1->cd();
  c1->SetLogy();
  TTree* tree = (TTree*) file->Get("g4sntuple");
  tree->Draw("Edep >> histo_energy(1000,0,2.5)");
  TH1D* histo_energy= (TH1D*)gDirectory->Get("histo_energy"); 
  histo_energy->SetLineColor(kRed);
  histo_energy->SetXTitle("energy [MeV]");
  histo_energy->SetYTitle("counts");
/*
  TLegend* legend = new TLegend(0.15, 0.7, 0.3, 0.85);
  legend->SetBorderSize(0);
  legend->AddEntry(histo_energy, "detector 1", "L");
  legend->AddEntry(tree, "detector 2", "L");
  legend->Draw();
*/


  TCanvas* c2 = new TCanvas("c2","c2", 0,0,900,800);
  c2->cd();
  c2->SetLogy();
  tree->Draw("KE >> histo_k(1000,0,2.5)");
  TH1D* histo_k= (TH1D*)gDirectory->Get("histo_k");
  histo_k->SetLineColor(kRed);

}

