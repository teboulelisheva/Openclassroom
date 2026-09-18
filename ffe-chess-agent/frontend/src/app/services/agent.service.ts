import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { AssistantResponse, Video } from '../models/assistant.model';

@Injectable({ providedIn: 'root' })
export class AgentService {
  private readonly base = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  /**
   * Appelle l'agent complet (LangGraph) pour une position FEN.
   * Le FEN contient des '/' (gardés) et des espaces (encodés en %20) :
   * encodeURI fait exactement ça et produit une URL valide.
   */
  getAssistant(fen: string): Observable<AssistantResponse> {
    const url = `${this.base}/assistant/${encodeURI(fen)}`;
    return this.http.get<AssistantResponse>(url);
  }

  /** Vidéos YouTube pour une ouverture (endpoint dédié). */
  getVideos(opening: string): Observable<{ videos: Video[] }> {
    const url = `${this.base}/videos/${encodeURIComponent(opening)}`;
    return this.http.get<{ videos: Video[] }>(url);
  }
}
