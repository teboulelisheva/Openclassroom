import { AfterViewInit, Component, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { NgxChessBoardModule, NgxChessBoardView } from 'ngx-chess-board';
import { AgentService } from './services/agent.service';
import { AssistantResponse } from './models/assistant.model';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, NgxChessBoardModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
})
export class AppComponent implements AfterViewInit {
  @ViewChild('board', { static: false }) board!: NgxChessBoardView;

  recommendations: AssistantResponse | null = null;
  loading = false;
  error: string | null = null;
  private lastFen = '';

  constructor(private agent: AgentService, private sanitizer: DomSanitizer) {}

  ngAfterViewInit(): void {
    // Analyse la position de départ au chargement.
    setTimeout(() => this.analyze(this.board.getFEN()), 0);
  }

  /** Déclenché à chaque coup joué sur l'échiquier. */
  onMove(): void {
    this.analyze(this.board.getFEN());
  }

  /** Appelle l'agent, en évitant les requêtes inutiles (même FEN). */
  private analyze(fen: string): void {
    if (!fen || fen === this.lastFen) {
      return;
    }
    this.lastFen = fen;
    this.loading = true;
    this.error = null;

    this.agent.getAssistant(fen).subscribe({
      next: (res) => {
        this.recommendations = res;
        this.loading = false;
      },
      error: () => {
        this.error =
          "Impossible de contacter l'agent. Vérifiez que le backend tourne sur http://localhost:8000.";
        this.loading = false;
      },
    });
  }

  reset(): void {
    this.board.reset();
    this.recommendations = null;
    this.error = null;
    this.lastFen = '';
    setTimeout(() => this.analyze(this.board.getFEN()), 0);
  }

  /** Autorise l'iframe YouTube (sécurité Angular). */
  safeEmbed(url: string): SafeResourceUrl {
    return this.sanitizer.bypassSecurityTrustResourceUrl(url);
  }

  hasErrors(): boolean {
    return !!this.recommendations?.errors?.length;
  }
}
